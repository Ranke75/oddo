# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from reportlab.graphics import barcode


class PickingBarcodeProductLines(models.TransientModel):
    _name = "picking.barcode.product.lines"

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True)
    lot_number = fields.Char(
        string='Lot/Serial Number')
    qty = fields.Integer(
        'Barcode Labels Qty',
        default=1,
        required=True)
    wizard_id = fields.Many2one(
        'picking.barcode.labels',
        string='Wizard')

class PickingBarcodeLabels(models.TransientModel):
    _name = "picking.barcode.labels"
    _description = 'Picking Barcode Labels'

    @api.model
    def default_get(self, fields):
        product_get_ids = []
        if self._context.get('active_model') == 'stock.picking':
            record_ids = self._context.get('active_ids', []) or []
            picking_ids = self.env['stock.picking'].browse(record_ids)
            product_get_ids = []
            pickiing_qty = 0
            for pack_operation in picking_ids.mapped('move_lines'):
                for pack in pack_operation.move_line_ids:
                    product_get_ids.append((0, 0, {
                        'product_id': pack_operation.product_id.id,
                        'lot_number': pack.lot_id.name,
                        'qty': 1.0
                    }))
                pickiing_qty += int(pack_operation.product_qty)
                for i in range(len(product_get_ids), pickiing_qty):
                    product_get_ids.append((0, 0, {
                        'product_id': pack_operation.product_id.id,
                        'qty': 1.0
                    }))
            view_id = self.env['ir.ui.view'].search([('name', '=', 'report_picking_barcode_labels')])
            if not view_id.arch:
                raise Warning('Someone has deleted the reference '
                    'view of report, Please Update the module!')
            return {
                'product_get_ids': product_get_ids
            }

    product_get_ids = fields.One2many(
        'picking.barcode.product.lines',
        'wizard_id',
        string='Products')

    @api.model
    def _create_paper_format(self, data):
        report_action_id = self.env['ir.actions.report'].search([('report_name', '=', 'picking_barcode_report.report_picking_barcode_labels')])
        if not report_action_id:
            raise Warning('Someone has deleted the reference view of report, Please Update the module!')
        config_rec = self.env['barcode.configuration'].search([], limit=1)
        if not config_rec:
            raise Warning(_(" Please configure barcode data from "
                            "configuration menu"))
        page_height = config_rec.label_height or 10
        page_width = config_rec.label_width or 10
        margin_top = config_rec.margin_top or 1
        margin_bottom = config_rec.margin_bottom or 1
        margin_left = config_rec.margin_left or 1
        margin_right = config_rec.margin_right or 1
        dpi = config_rec.dpi or 90
        header_spacing = config_rec.header_spacing or 1
        orientation = 'Portrait'
        self._cr.execute(""" DELETE FROM report_paperformat WHERE custom_report=TRUE""")
        paperformat_id = self.env['report.paperformat'].create({
                'name': 'Custom Report',
                'format': 'custom',
                'page_height': page_height,
                'page_width': page_width,
                'dpi': dpi,
                'custom_report': True,
                'margin_top': margin_top,
                'margin_bottom': margin_bottom,
                'margin_left': margin_left,
                'margin_right': margin_right,
                'header_spacing': header_spacing,
                'orientation': orientation,
                #'display_height': config_rec.display_height,
                #'display_width': config_rec.display_width,
                #'humanreadable': config_rec.humanreadable,
                #'lot': config_rec.lot
                })
        report_action_id.write({'paperformat_id': paperformat_id.id})
        return True

    @api.multi
    def print_picking_barcode(self):
        if not self.env.user.has_group('dynamic_barcode_labels.group_barcode_labels'):
            raise Warning(_("You have not enough rights to access this "
                            "document.\n Please contact administrator to access "
                            "this document."))
        if not self.product_get_ids:
            raise Warning(_(""" There is no product lines to print."""))
        config_rec = self.env['barcode.configuration'].search([], limit=1)
        if not config_rec:
            raise Warning(_(" Please configure barcode data from "
                            "configuration menu"))
        datas = {
                 'ids': [x.product_id.id for x in self.product_get_ids],
                 'model': 'product.product',
                 'form': {
                    'label_width': config_rec.label_width or 50,
                    'label_height': config_rec.label_height or 50,
                    'margin_top': config_rec.margin_top or 1,
                    'margin_bottom': config_rec.margin_bottom or 1,
                    'margin_left': config_rec.margin_left or 1,
                    'margin_right': config_rec.margin_right or 1,
                    'dpi': config_rec.dpi or 90,
                    'header_spacing': config_rec.header_spacing or 1,
                    'barcode_height': config_rec.barcode_height or 300,
                    'barcode_width': config_rec.barcode_width or 1500,
                    'barcode_type': config_rec.barcode_type or 'EAN13',
                    'barcode_field': config_rec.barcode_field or '',
                    'display_width': config_rec.display_width,
                    'display_height': config_rec.display_height,
                    'humanreadable': config_rec.humanreadable,
                    'product_name': config_rec.product_name,
                    'product_variant': config_rec.product_variant,
                    'price_display': config_rec.price_display,
                    'lot': config_rec.lot,
                    'product_code': config_rec.product_code or '',
                    'barcode': config_rec.barcode,
                    'currency_position': config_rec.currency_position or 'after',
                    'currency': config_rec.currency and config_rec.currency.id or '',
                    'symbol': config_rec.currency and config_rec.currency.symbol or '',
                    'company_id': self.env.user.company_id.id,
                    'product_ids': [{
                        'product_id': line.product_id.id,
                        'lot_number': line.lot_number or '',
                        'qty': line.qty,
                        } for line in self.product_get_ids]
                      }
                 }
        browse_pro = self.env['product.product'].browse([x.product_id.id for x in self.product_get_ids])
        for product in browse_pro:
            barcode_value = product[config_rec.barcode_field]
            if not barcode_value:
                raise Warning(_('Please define barcode for %s!' % (product['name'])))
            try:
                barcode.createBarcodeDrawing(
                            config_rec.barcode_type,
                            value=barcode_value,
                            format='png',
                            width=int(config_rec.barcode_height),
                            height=int(config_rec.barcode_width),
                            humanReadable=config_rec.humanreadable or False
                            )
            except:
                raise Warning('Select valid barcode type according barcode field value or check value in field!')

        self.sudo()._create_paper_format(datas['form'])
        return self.env.ref('picking_barcode_report.pickingbarcodelabels').report_action([], data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
