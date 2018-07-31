# -*- coding: utf-8 -*-

from odoo import models, api, _
from reportlab.graphics import barcode
from base64 import b64encode


class ReportPickingBarcodeLabels(models.AbstractModel):
    _name = 'report.picking_barcode_report.report_picking_barcode_labels'

    @api.model
    def get_report_values(self, docids, data=None):
        picking_barcode_report = self.env['ir.actions.report']._get_report_from_name('picking_barcode_report.report_picking_barcode_labels')
        docids = data['context']['active_ids']
        picking_barcodes = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids':  data['form']['product_ids'],
            'doc_model': picking_barcode_report.model,
            'docs': docids,
            'data': data,
            'get_barcode_string': self._get_barcode_string,
        }

    @api.model
    def _get_barcode_string(self, product, data):
        barcode_value = product[str(data['form']['barcode_field'])]
        barcode_str = barcode.createBarcodeDrawing(
            data['form']['barcode_type'],
            value=barcode_value,
            format='png',
            width=int(data['form']['barcode_height']),
            height=int(data['form']['barcode_width']),
            humanReadable=data['form']['humanreadable']
        )
        encoded_string = b64encode(barcode_str.asString('png'))
        barcode_str = "<img style='width:" + str(data['form']['display_width']) + "px;height:" + str(data['form']['display_height']) + "px'src='data:image/png;base64,{0}'>".format(str(encoded_string))
        return barcode_str or ''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
