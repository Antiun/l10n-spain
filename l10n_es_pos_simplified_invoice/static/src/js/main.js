/**
 * # -*- encoding: utf-8 -*-
 * ##############################################################################
 * #
 * #    OpenERP, Open Source Management Solution
 * #    This module copyright :
 * #        (c) 2014 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
 * #                 Antonio Espinosa <antonioea@antiun.com>
 * #
 * #    This program is free software: you can redistribute it and/or modify
 * #    it under the terms of the GNU Affero General Public License as
 * #    published by the Free Software Foundation, either version 3 of the
 * #    License, or (at your option) any later version.
 * #
 * #    This program is distributed in the hope that it will be useful,
 * #    but WITHOUT ANY WARRANTY; without even the implied warranty of
 * #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * #    GNU Affero General Public License for more details.
 * #
 * #    You should have received a copy of the GNU Affero General Public License
 * #    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * #
 * ##############################################################################
 */

// Check jQuery available
if (typeof jQuery === 'undefined') { throw new Error('l10n_es POS Simplified invoice Addon requires jQuery') }

+function ($) {
    'use strict';

    openerp.l10n_es_pos_simplified_invoice = function (instance) {
        var _t = instance.web._t,
            _lt = instance.web._lt;
        var QWeb = instance.web.qweb;

        // Widget: ScreenWidget
        instance.point_of_sale.PaymentScreenWidget.include({
            // Disable validation if total due is over 400,00 €
            update_payment_summary: function() {
                var currentOrder = this.pos.get('selectedOrder');
                var dueTotal = currentOrder.getTotalTaxIncluded();
                this._super.apply(this, arguments);
                if(this.pos_widget.action_bar){
                    if (dueTotal > 400){
                        this.pos_widget.action_bar.set_button_disabled('validation', true);
                    }
                }
            },
            // Disable validation if total due is over 400,00 €
            validate_order: function() {
                var currentOrder = this.pos.get('selectedOrder');
                var dueTotal = currentOrder.getTotalTaxIncluded();
                this._super.apply(this, arguments);
                if(this.pos_widget.action_bar){
                    if (dueTotal > 400){
                        this.pos_widget.action_bar.set_button_disabled('validation', true);
                    }
                }
            },
        });

    };


}(jQuery);
