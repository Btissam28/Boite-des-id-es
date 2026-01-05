from odoo import models, fields, api

class TpIdeeHistorique(models.Model):
    _name = "tp.idee.historique"
    _description = "Historique des changements de statut"
    _order = "date_changement desc"

    idee_id = fields.Many2one(
        "tp.idee",
        string="Idée",
        required=True,
        ondelete="cascade"
    )
    ancien_statut = fields.Selection(
        [
            ("brouillon", "Brouillon"),
            ("en_cours", "En cours d'évaluation"),
            ("acceptee", "Acceptée"),
            ("refusee", "Refusée"),
        ],
        string="Ancien statut"
    )
    nouveau_statut = fields.Selection(
        [
            ("brouillon", "Brouillon"),
            ("en_cours", "En cours d'évaluation"),
            ("acceptee", "Acceptée"),
            ("refusee", "Refusée"),
        ],
        string="Nouveau statut",
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Utilisateur",
        required=True,
        default=lambda self: self.env.user
    )
    date_changement = fields.Datetime(
        string="Date du changement",
        default=fields.Datetime.now,
        required=True
    )
    commentaire = fields.Text(string="Commentaire")



