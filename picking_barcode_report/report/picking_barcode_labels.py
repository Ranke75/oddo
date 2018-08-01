# -*- coding: utf-8 -*-

import time
from odoo import models, api, _
from reportlab.graphics import barcode
from base64 import b64encode


class ReportPickingBarcodeLabels(models.AbstractModel):
    _name = 'report.picking_barcode_report.report_picking_barcode_labels'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        picking_barcode_report = self.env['ir.actions.report']._get_report_from_name('picking_barcode_report.report_picking_barcode_labels')
        docids = data['context']['active_ids']
        picking_barcodes = self.env['stock.picking'].browse(docids)

        return {
            'doc_ids':  data['form']['product_ids'],
            'doc_model': picking_barcode_report.model,
            'docs': docids,
            'data': data,
            'get_barcode_value': self.get_barcode_value,
            'is_humanreadable': self.is_humanreadable,
            'time': time,
        }

    def is_humanreadable(self, data):
        return data['form']['humanreadable'] and 1 or 0

    def get_barcode_value(self, product, data):
        barcode_value = product[str(data['form']['barcode_field'])]
        return barcode_value


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: