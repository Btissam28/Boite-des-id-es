# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TpIdeeCategorie(models.Model):
    _name = 'tp.idee.categorie'
    _description = 'Catégorie d\'idée'
    _order = 'sequence, name'

    name = fields.Char(string="Nom", required=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Séquence", default=10, help="Ordre d'affichage")
    
    # Relations
    idee_ids = fields.One2many(
        'tp.idee',
        'categorie_id',
        string="Idées"
    )
    
    idee_count = fields.Integer(
        string="Nombre d'idées",
        compute='_compute_idee_count',
        store=False
    )
    
    @api.depends('idee_ids')
    def _compute_idee_count(self):
        """Calcule le nombre d'idées dans cette catégorie"""
        for record in self:
            record.idee_count = len(record.idee_ids)
