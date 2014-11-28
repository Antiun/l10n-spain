# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#    Copyright (c) 2010 Pexego Sistemas Informáticos S.L. (http://www.pexego.es)
#    @authors: Jordi Esteve (Zikzakmedia), Borja López Soilán (Pexego)
#    Copyright (c) 2014 Txerpa - Biel Massot (https://www.txerpa.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging

class WizardLog:
    """
    *******************************************************************
    Small helper class to store the messages and errors on the wizard.
    *******************************************************************
    """
    def __init__(self):
        self.messages = []
        self.errors = []

    def add(self, message, is_error=False):
        """
        Adds a message to the log.
        """
        logger = logging.getLogger("account_chart_update")
        if is_error:
            logger.warning(u"Log line: %s" % message)
            self.errors.append(message)
        else:
            logger.debug(u"Log line: %s" % message)
        self.messages.append(message)

    def has_errors(self):
        """
        Returns whether errors where logged.
        """
        return self.errors

    def __call__(self):
        return "".join(self.messages)

    def __str__(self):
        return "".join(self.messages)

    def get_errors_str(self):
        return "".join(self.errors)

class wizard_chart_update(orm.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    _columns = {
        'update_casilla': fields.boolean('Update Casillas AEAT and 303'),
        'casilla_ids': fields.one2many('wizard.update.charts.accounts.casilla', 'update_chart_wizard_id', 'Casilla', ondelete='cascade'),
        'new_casillas': fields.integer('New Casillas', readonly=True),
        'updated_casillas': fields.integer('Updated Casillas', readonly=True),
        'modelo303_ids': fields.one2many('wizard.update.charts.accounts.modelo303', 'update_chart_wizard_id', 'Modelo303', ondelete='cascade'),
        'new_modelos303': fields.integer('New Modelos303', readonly=True),
        'updated_modelos303': fields.integer('Updated Modelos303', readonly=True),
    }
    
    _defaults = {
        'update_casilla': True,
    }

    def _map_modelo303_template(self, cr, uid, wizard, modelo303_template_mapping, modelo303_template, context=None):
        """
        Adds a modelo303 template -> modelo303 id to the mapping.
        """
        if modelo303_template and not modelo303_template_mapping.get(modelo303_template.id):
            modelos303 = self.pool.get('l10n.es.aeat.modelo303')
            modelos303_ids = modelos303.search(cr, uid, [
                ('name', '=', modelo303_template.name),
                # ('company_id', '=', wizard.company_id.id) # TODO
            ], context=context)
            if modelos303_ids:
                modelo303_template_mapping[modelo303_template.id] = modelos303_ids[0]

    def _map_casilla_template(self, cr, uid, wizard, casilla_template_mapping, casilla_template, context=None):
        """
        Adds a casilla template -> casilla id to the mapping.
        """
        if casilla_template and not casilla_template_mapping.get(casilla_template.id):
            casillas = self.pool.get('l10n.es.aeat.modelo303.casilla')
            casilla_ids = casillas.search(cr, uid, [
                ('name', '=', casilla_template.name),
                ('modelo303_id.name', '=', casilla_template.modelo303_id.name)
                # ('company_id', '=', wizard.company_id.id) # TODO
            ], context=context)
            if casilla_ids:
                casilla_template_mapping[casilla_template.id] = casilla_ids[0]

    def _find_modelos303(self, cr, uid, wizard, context=None):
        """
        Search for, and load, modelo303 templates to create/update.
        """
        new_modelos303 = 0
        updated_modelos303 = 0
        modelo303_template_mapping = {}

        modelos303 = self.pool.get('l10n.es.aeat.modelo303')
        m303_template = self.pool.get('l10n.es.aeat.modelo303.template')
        wiz_modelos303 = self.pool.get('wizard.update.charts.accounts.modelo303')

        # Remove previous taxes
        wiz_modelos303.unlink(cr, uid, wiz_modelos303.search(cr, uid, []))
        # Search for new / updated taxes
        for modelo303_template in m303_template.browse(cr, uid, m303_template.search(cr, uid, [])):#wizard.chart_template_id.modelo303_template_ids:
            # Ensure the tax template is on the map (search for the mapped tax
            # id).
            self._map_modelo303_template(
                cr, uid, wizard, modelo303_template_mapping, modelo303_template, context)

            modelo303_id = modelo303_template_mapping.get(modelo303_template.id)
            if not modelo303_id:
                new_modelos303 += 1
                vals_wiz = {
                    'modelo303_id': modelo303_template.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                }
                wiz_modelos303.create(cr, uid, vals_wiz, context)
            elif wizard.update_casilla:
                # Check the tax for changes.
                modified = False
                notes = ""
                modelo303 = modelos303.browse(cr, uid, modelo303_id, context=context)
                if modelo303.date != modelo303_template.date:
                    notes += _("The date field is different.\n")
                    modified = True
                if modelo303.template != modelo303_template.template:
                    notes += _("The template field is different.\n")
                    modified = True

                if modified:
                    # Tax to update.
                    updated_modelos303 += 1
                    wiz_modelos303.create(cr, uid, {
                        'modelo303_id': modelo303_template.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_modelo303_id': modelo303_id,
                        'notes': notes,
                    }, context)

        return {'new': new_modelos303, 'updated': updated_modelos303, 'mapping': modelo303_template_mapping}

    def _find_casillas(self, cr, uid, wizard, context=None):
        """
        Search for, and load, casillas templates to create/update.
        """
        new_casillas = 0
        updated_casillas = 0
        casilla_template_mapping = {}

        casillas = self.pool.get('l10n.es.aeat.modelo303.casilla')
        c_template = self.pool.get('l10n.es.aeat.modelo303.casilla.template')
        wiz_casillas = self.pool.get('wizard.update.charts.accounts.casilla')

        # Remove previous taxes
        wiz_casillas.unlink(cr, uid, wiz_casillas.search(cr, uid, []))
        # Search for new / updated taxes
        for casilla_template in c_template.browse(cr, uid, c_template.search(cr, uid, [])):#wizard.chart_template_id.casilla_template_ids:
            # Ensure the tax template is on the map (search for the mapped tax
            # id).
            self._map_casilla_template(
                cr, uid, wizard, casilla_template_mapping, casilla_template, context)

            casilla_id = casilla_template_mapping.get(casilla_template.id)
            if not casilla_id:
                new_casillas += 1
                vals_wiz = {
                    'casilla_id': casilla_template.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                }
                wiz_casillas.create(cr, uid, vals_wiz, context)
            elif wizard.update_casilla:
                # Check the tax for changes.
                modified = False
                notes = ""
                casilla = casillas.browse(cr, uid, casilla_id, context=context)
                if casilla.code != casilla_template.code:
                    notes += _("The code field is different.\n")
                    modified = True
                if casilla.evaluate_as != casilla_template.evaluate_as:
                    notes += _("The evaluate_as field is different.\n")
                    modified = True
                if casilla.tax_code_ids != casilla_template.tax_code_ids:
                    notes += _("The tax_codes_ids field is different.\n")
                    modified = True
                if casilla.default_value != casilla_template.default_value:
                    notes += _("The default_value field is different.\n")
                    modified = True
                # TODO: We could check other tax fields for changes...

                if modified:
                    # Tax to update.
                    updated_casillas += 1
                    wiz_casillas.create(cr, uid, {
                        'casilla_id': casilla_template.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_casilla_id': casilla_id,
                        'notes': notes,
                    }, context)

        return {'new': new_casillas, 'updated': updated_casillas, 'mapping': casilla_template_mapping}


    def action_find_records(self, cr, uid, ids, context=None):
        """
        Searchs for records to update/create and shows them
        """
        rdo = super(wizard_chart_update, self).action_find_records(cr, uid, ids, context)
        if context is None:
            context = {}
        
        wizard = self.browse(cr, uid, ids[0], context=context)

        if wizard.lang:
            context['lang'] = wizard.lang
        elif context.get('lang'):
            del context['lang']

        # Search for, and load, the records to create/update.
        m303_res = self._find_modelos303(cr, uid, wizard, context=context)
        casillas_res = self._find_casillas(cr, uid, wizard, context=context)

        # Write the results, and go to the next step.
        self.write(cr, uid, [wizard.id], {
            'state': 'ready',
            'new_modelos303': m303_res.get('new', 0),
            'new_casillas': casillas_res.get('new', 0),
            'updated_modelos303': m303_res.get('updated', 0),
            'updated_casillas': casillas_res.get('updated', 0),
        }, context)

        return rdo

    def _update_modelos303(self, cr, uid, wizard, log, context=None):
        """
        Update modelos303 with modelos303 templates
        """
        modelos303 = self.pool.get('l10n.es.aeat.modelo303')

        new_modelos303 = 0
        updated_modelos303 = 0

        for wiz_modelo303 in wizard.modelo303_ids:
            modelo303_template = wiz_modelo303.modelo303_id
            modelo303_id = None
            modified = False
            if wiz_modelo303.type == 'new':
                # Create a new fiscal position
                vals_modelo303 = {
                    # 'company_id': wizard.company_id.id, # TODO
                    'name': modelo303_template.name,
                    'date': modelo303_template.date,
                    'template': modelo303_template.template,
                }
                modelo303_id = modelos303.create(cr, uid, vals_modelo303)
                new_modelos303 += 1
                modified = True
            elif wizard.update_casilla and wiz_modelo303.update_modelo303_id:
                # Update the given fiscal position (remove the tax and account
                # mappings, that will be regenerated later)
                modelo303_id = wiz_modelo303.update_modelo303_id.id
                vals_modelo303 = {
                    'name': modelo303_template.name,
                    'date': modelo303_template.date,
                    'template': modelo303_template.template,
                }
                try:
                    modelos303.write(cr, uid, [modelo303_id], vals_modelo303)
                    log.add(_("Updated modelos303 %s.\n") % modelo303_template.name)
                    updated_modelos303 += 1
                    modified = True
                except orm.except_orm, ex:
                    log.add(_("Exception writing modelo303 %s: %s - %s.\n")
                            % (modelo303_template.name, ex.name, ex.value), True)
            #else:
            #    modelo303_id = wiz_modelo303.update_modelo303_id and wiz_modelo303.update_modelo303_id.id

            log.add(_("Created or updated modelo303 %s.\n")
                    % modelo303_template.name)
        return {'new': new_modelos303, 'updated': updated_modelos303}

    def _update_casillas(self, cr, uid, wizard, log, context=None):
        """
        Update casillas with casillas templates
        """
        tax_code = self.pool.get('account.tax.code')
        casillas = self.pool.get('l10n.es.aeat.modelo303.casilla')
        modelo303 = self.pool.get('l10n.es.aeat.modelo303')

        new_casillas = 0
        updated_casillas = 0

        for wiz_casilla in wizard.casilla_ids:
            casilla_template = wiz_casilla.casilla_id
            casilla_id = None
            modified = False
            modelo303_ids = modelo303.search(cr, uid, [('name', '=', casilla_template.modelo303_id.name)])
            tax_code_ids = []
            if casilla_template.tax_code_ids:
                tax_code_ids = tax_code.search(cr, uid, [('name', 'in', [tc.name for tc in casilla_template.tax_code_ids]), ('company_id', '=', wizard.company_id.id)])
            if wiz_casilla.type == 'new':
                # Create a new fiscal position
                vals_casilla = {
                    # 'company_id': wizard.company_id.id, # TODO
                    'modelo303_id': modelo303_ids[0],
                    'name': casilla_template.name,
                    'code': casilla_template.code,
                    'tax_code_ids': [(6,0, tax_code_ids)],
                    'evaluate_as': casilla_template.evaluate_as,
                    'default_value': casilla_template.default_value
                }
                casilla_id = casillas.create(cr, uid, vals_casilla)
                new_casillas += 1
                modified = True
            elif wizard.update_casilla and wiz_casilla.update_casilla_id:
                # Update the given fiscal position (remove the tax and account
                # mappings, that will be regenerated later)
                casilla_id = wiz_casilla.update_casilla_id.id
                vals_casilla = {
                    # 'company_id': wizard.company_id.id, # TODO
                    'modelo303_id': modelo303_ids[0],
                    'name': casilla_template.name,
                    'code': casilla_template.code,
                    'tax_code_ids': [(6,0, tax_code_ids)],
                    'evaluate_as': casilla_template.evaluate_as,
                    'default_value': casilla_template.default_value
                }
                try:
                    casillas.write(cr, uid, [casilla_id], vals_casilla)
                    log.add(_("Updated casillas %s.\n") % casilla_template.name)
                    updated_casillas += 1
                    modified = True
                except orm.except_orm, ex:
                    log.add(_("Exception writing casilla %s: %s - %s.\n")
                            % (casilla_template.name, ex.name, ex.value), True)
            #else:
            #    casilla_id = wiz_casilla.update_casilla_id and wiz_casilla.update_casilla_id.id

            log.add(_("Created or updated casilla %s.\n")
                    % casilla_template.name)
        return {'new': new_casillas, 'updated': updated_casillas}

    def action_update_records(self, cr, uid, ids, context=None):
        """
        Action that creates/updates the selected elements.
        """
        rdo = super(wizard_chart_update, self).action_update_records(cr, uid, ids, context)
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)

        if wizard.lang:
            context['lang'] = wizard.lang
        elif context.get('lang'):
            del context['lang']

        log = WizardLog()

        # Create or update the records.       
        m303_res = self._update_modelos303(cr, uid, wizard, log, context=context)
        casillas_res = self._update_casillas(cr, uid, wizard, log, context=context)

        # Check if errors where detected and wether we should stop.
        if log.has_errors() and not wizard.continue_on_errors:
            raise orm.except_orm(_('Error'), _(
                "One or more errors detected!\n\n%s") % log.get_errors_str())

        # Store the data and go to the next step.
        self.write(cr, uid, [wizard.id], {
            'new_modelos303': m303_res.get('new', 0),
            'new_casillas': casillas_res.get('new', 0),
            'updated_modelos303': m303_res.get('updated', 0),
            'updated_casillas': casillas_res.get('updated', 0),
            'log': log(),
        }, context)

        return rdo


class wizard_update_charts_accounts_modelo303(orm.TransientModel):
    """
    **************************************************************************
    Modelo 303 that needs to be updated (new or updated in the template).
    **************************************************************************
    """
    _name = 'wizard.update.charts.accounts.modelo303'
    _columns = {
        'modelo303_id': fields.many2one('l10n.es.aeat.modelo303.template', 'Casillas template', required=True, ondelete='set null'),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True, ondelete='cascade'),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_modelo303_id': fields.many2one('l10n.es.aeat.modelo303', 'Modelo303 to update', required=False, ondelete='set null'),
        'notes': fields.text('Notes'),
    }
    _defaults = {
    }
    

class wizard_update_charts_accounts_casilla(orm.TransientModel):
    """
    **************************************************************************
    Casillas AEAT that needs to be updated (new or updated in the template).
    **************************************************************************
    """
    _name = 'wizard.update.charts.accounts.casilla'
    _columns = {
        'casilla_id': fields.many2one('l10n.es.aeat.modelo303.casilla.template', 'Casillas template', required=True, ondelete='set null'),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True, ondelete='cascade'),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_casilla_id': fields.many2one('l10n.es.aeat.modelo303.casilla', 'Casilla to update', required=False, ondelete='set null'),
        'notes': fields.text('Notes'),
    }
    _defaults = {
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
