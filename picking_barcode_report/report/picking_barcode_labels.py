# -*- coding: utf-8 -*-

from odoo import models, api, _
from reportlab.graphics import barcode
from base64 import b64encode


class ReportPickingBarcodeLabels(models.AbstractModel):
    _name = 'report.picking_barcode_report.report_picking_barcode_labels'

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
              'picking_barcode_report.report_picking_barcode_labels')
        docargs = {
            'doc_ids': data['form']['product_ids'],
            'doc_model': report.model,
            'docs': docids,
            'get_barcode_string': self._get_barcode_string,
            'data': data
            }
        return report_obj.render(
             'picking_barcode_report.report_picking_barcode_labels', docargs)

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
        barcode_str = "<img style='width:" + str(data['form']['display_width']) + "px;height:" + str(data['form']['display_height']) + "px'src='data:image/png;base64,{0}'>".format(encoded_string)
        return barcode_str or ''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: