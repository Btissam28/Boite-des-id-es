from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class TpIdeeComment(models.Model):
    _name = "tp.idee.comment"
    _description = "Commentaire sur une idée"
    _order = "date_commentaire desc"

    idee_id = fields.Many2one(
        "tp.idee",
        string="Idée",
        required=True,
        ondelete="cascade"
    )
    user_id = fields.Many2one(
        "res.users",
        string="Utilisateur",
        required=True,
        default=lambda self: self.env.user
    )
    commentaire = fields.Text(string="Commentaire", required=True)
    note = fields.Integer(
        string="Note",
        default=0,
        help="Note de 1 à 5 étoiles"
    )
    date_commentaire = fields.Datetime(
        string="Date du commentaire",
        default=fields.Datetime.now,
        required=True
    )

    @api.constrains('note')
    def _check_note(self):
        for record in self:
            if record.note < 0 or record.note > 5:
                raise models.ValidationError("La note doit être entre 0 et 5")

    @api.constrains('idee_id', 'user_id')
    def _check_cannot_comment_own_idea(self):
        """Empêche un utilisateur de commenter ses propres idées"""
        for record in self:
            if record.idee_id and record.idee_id.propose_par and record.user_id:
                if record.idee_id.propose_par == record.user_id.name:
                    raise UserError("Vous ne pouvez pas commenter vos propres idées. Vous pouvez uniquement commenter les idées des autres employés.")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create pour vérifier qu'on ne commente pas ses propres idées"""
        # Vérifier avant la création
        for vals in vals_list:
            # S'assurer que user_id est défini
            if 'user_id' not in vals:
                vals['user_id'] = self.env.user.id
            
            # Vérifier si on essaie de commenter sa propre idée
            if 'idee_id' in vals:
                idee = self.env['tp.idee'].browse(vals['idee_id'])
                if idee.exists():
                    user = self.env['res.users'].browse(vals['user_id'])
                    if idee.propose_par and user.exists() and idee.propose_par == user.name:
                        raise UserError("Vous ne pouvez pas commenter vos propres idées. Vous pouvez uniquement commenter les idées des autres employés.")
        return super(TpIdeeComment, self).create(vals_list)



