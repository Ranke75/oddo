# -*- coding: utf-8 -*-
from odoo import models, api, fields
import datetime
import dateutil.relativedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('property_cost_method', 'categ_id.property_cost_method')
    def _compute_cost_method(self):
        cost_method = 'average'
        if self.tracking == 'lot':
            cost_method = 'standard'
        self.cost_method = cost_method or self.categ_id.property_cost_method

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def product_price_update_after_done(self):
        ''' inherit method for cost calculate base on purchase'''
        to_update_moves = self.filtered(lambda move: move.location_dest_id.usage == 'internal')
        to_update_moves._store_average_cost_price()

    # @api.multi
    # def action_done(self):
    #     result = super(StockMove, self).action_done()
    #     location_obj = self.env['stock.location']
    #     parent_id = location_obj.search([('name', '=', 'ATL')])
    #     stock_location_id = location_obj.search([('name', '=', 'Stock'), ('location_id', '=', parent_id.id)])
    #     vendor_location_id = location_obj.search([('name', '=', 'Suppliers'), ('usage', '=', 'supplier')])
    #     product = self.product_id[:1]
    #     quants = self.env['stock.quant'].search([('product_id', '=', product.id),
    #         ('location_id', '=', stock_location_id.id)])
    #     if quants:
    #         inv_qty = inv_value = value = purchase_qty = purchase_value = 0.0
    #         for quant in quants:
    #             inv_qty += quant.qty #On hand Qty
    #             inv_value += quant.inventory_value #On hand inventory value
    #             for history in quant.history_ids.filtered(lambda s: s.location_id == vendor_location_id 
    #                 and s.location_dest_id == stock_location_id):
    #                 if history.group_id and history.purchase_line_id:
    #                     purchase_value += quant.qty * history.purchase_line_id.price_unit # inventory value base on purchase price unit
    #         if product.tracking == 'none':
    #             if purchase_value > 0 and inv_qty > 0:
    #                 product.standard_price = float(purchase_value/inv_qty)
    #             else:
    #                 product.standard_price = 0.0
    #         elif product.tracking == 'serial':
    #             if purchase_value > 0 and inv_qty > 0:
    #                 product.standard_price = float(purchase_value/inv_qty)
    #             else:
    #                 product.standard_price = 0.0
    #     return result


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def update_cost_price(self):
        DF = '%Y-%m-%d %H:%M:%S'
        currentdate = datetime.datetime.now()
        start_date = currentdate - dateutil.relativedelta.relativedelta(days=365)
        location_obj = self.env['stock.location']
        parent_id = location_obj.search([('name', '=', 'ATL')])
        stock_location_id = location_obj.search([('name', '=', 'Stock'), ('location_id', '=', parent_id.id)])
        vendor_location_id = location_obj.search([('name', '=', 'Suppliers'), ('usage', '=', 'supplier')])
        for record in self.search([]):
            quants = self.env['stock.quant'].search([('product_id', '=', record.id),
                ('location_id', '=', stock_location_id.id)])
            if quants:
                inv_qty = inv_value = value = purchase_qty = purchase_value = 0.0
                for quant in quants:
                    inv_qty += quant.qty #On hand Qty
                    inv_value += quant.inventory_value #On hand inventory value
                    for history in quant.history_ids.filtered(lambda s: s.location_id == vendor_location_id 
                        and s.location_dest_id == stock_location_id):
                        if history.group_id and history.purchase_line_id:
                            # purchase = self.env['purchase.order'].search([
                            #     ('name','=', history.group_id.name),
                            #     ('date_order', '>=', start_date.strftime(DF))])
                            #purchase = self.env['purchase.order'].search([
                            #    ('name','=', history.group_id.name)])
                            #for line in purchase.order_line.filtered(lambda p: p.product_id.id == record.id):
                            #    value = line.price_unit #Last purchase price
                            #    purchase_qty += quant.qty #Qty base on purchase
                            #    purchase_value += quant.qty * line.price_unit # inventory value base on purchase price unit
                            purchase_qty += quant.qty #Qty base on purchase
                            purchase_value += quant.qty * history.purchase_line_id.price_unit # inventory value base on purchase price unit
                if record.tracking == 'none':
                    if purchase_value > 0 and inv_qty > 0:
                        record.standard_price = float(purchase_value/inv_qty)
                        # record.standard_price = float(purchase_value/purchase_qty)
                    else:
                        record.standard_price = 0.0
                elif record.tracking == 'serial':
                    if purchase_value > 0 and inv_qty > 0:
                        record.standard_price = float(purchase_value/inv_qty)
                        # record.standard_price = value
                    else:
                        record.standard_price = 0.0
            else:
                record.standard_price = 0.0

class Quant(models.Model):
    _inherit = "stock.quant"

    @api.multi
    def _compute_inventory_value(self):
        location_obj = self.env['stock.location']
        parent_id = location_obj.search([('name', '=', 'ATL')])
        stock_location_id = location_obj.search([('name', '=', 'Stock'), ('location_id', '=', parent_id.id)])
        vendor_location_id = location_obj.search([('name', '=', 'Suppliers'), ('usage', '=', 'supplier')])
        for quant in self:
            if quant.company_id != self.env.user.company_id:
                # if the company of the quant is different than the current user company, force the company in the context
                # then re-do a browse to read the property fields for the good company.
                quant = quant.with_context(force_company=quant.company_id.id)
            for history in quant.history_ids.filtered(lambda s: s.location_id == vendor_location_id 
                and s.location_dest_id == stock_location_id):
                if history.group_id and history.purchase_line_id:
                    quant.inventory_value = history.purchase_line_id.price_unit * quant.qty
                    # purchase = self.env['purchase.order'].search([
                    #     ('name','=', history.group_id.name)])
                    # for line in purchase.order_line.filtered(lambda p: p.product_id.id == quant.product_id.id):
                    #     quant.inventory_value = line.price_unit * quant.qty
