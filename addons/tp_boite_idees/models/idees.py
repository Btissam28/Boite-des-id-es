from odoo import models, fields, api
from odoo.exceptions import UserError

class TpIdee(models.Model):
    _name = "tp.idee"
    _description = "Boîte à Idées"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Titre de l'idée", required=True, tracking=True)
    description = fields.Text(string="Description")
    propose_par = fields.Char(string="Proposé par")
    date_soumission = fields.Date(
        string="Date de soumission",
        default=fields.Date.context_today
    )
    statut = fields.Selection(
        [
            ("brouillon", "Brouillon"),
            ("en_cours", "En cours d'évaluation"),
            ("acceptee", "Acceptée"),
            ("refusee", "Refusée"),
        ],
        string="Statut",
        default="brouillon",
        tracking=True
    )
    
    # Nouveaux champs de catégorisation
    categorie_id = fields.Many2one(
        "tp.idee.categorie",
        string="Catégorie"
    )
    priorite = fields.Selection(
        [
            ("low", "Faible"),
            ("medium", "Moyenne"),
            ("high", "Haute"),
            ("urgent", "Urgente"),
        ],
        string="Priorité",
        default="medium"
    )
    tag_ids = fields.Many2many(
        "res.partner.category",
        "tp_idee_tag_rel",
        "idee_id",
        "tag_id",
        string="Tags"
    )
    
    # Workflow d'approbation
    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        tracking=True
    )
    
    # Système de vote et notation
    vote_count = fields.Integer(
        string="Nombre de votes",
        compute="_compute_vote_count",
        store=False
    )
    note_moyenne = fields.Float(
        string="Note moyenne",
        compute="_compute_note_moyenne",
        digits=(2, 1)
    )
    
    # Relations
    comment_ids = fields.One2many(
        "tp.idee.comment",
        "idee_id",
        string="Commentaires"
    )
    historique_ids = fields.One2many(
        "tp.idee.historique",
        "idee_id",
        string="Historique"
    )
    
    # Méthodes compute
    @api.depends('comment_ids.note')
    def _compute_vote_count(self):
        for record in self:
            record.vote_count = len(record.comment_ids.filtered(lambda c: c.note > 0))
    
    @api.depends('comment_ids.note')
    def _compute_note_moyenne(self):
        for record in self:
            notes = record.comment_ids.mapped('note')
            notes_filtered = [n for n in notes if n > 0]
            if notes_filtered:
                record.note_moyenne = sum(notes_filtered) / len(notes_filtered)
            else:
                record.note_moyenne = 0.0
    
    # Méthodes d'action pour le workflow
    def action_soumettre(self):
        """Soumet l'idée pour évaluation"""
        for record in self:
            if record.statut != "brouillon":
                raise UserError("Seules les idées en brouillon peuvent être soumises.")
            record.write({'statut': 'en_cours'})
        return True
    
    def action_approuver(self):
        """Approuve l'idée"""
        # Vérifier que l'utilisateur a les droits de responsable ou admin
        if not (self.env.user.has_group('tp_boite_idees.group_tp_idee_manager') or 
                self.env.user.has_group('tp_boite_idees.group_tp_idee_admin')):
            raise UserError("Vous n'avez pas les droits pour approuver des idées. Seuls les responsables et administrateurs peuvent approuver.")
        
        for record in self:
            if record.statut != "en_cours":
                raise UserError("Seules les idées en cours d'évaluation peuvent être approuvées.")
            record.write({'statut': 'acceptee'})
        return True
    
    def action_rejeter(self):
        """Rejette l'idée"""
        # Vérifier que l'utilisateur a les droits de responsable ou admin
        if not (self.env.user.has_group('tp_boite_idees.group_tp_idee_manager') or 
                self.env.user.has_group('tp_boite_idees.group_tp_idee_admin')):
            raise UserError("Vous n'avez pas les droits pour rejeter des idées. Seuls les responsables et administrateurs peuvent rejeter.")
        
        for record in self:
            if record.statut not in ["brouillon", "en_cours"]:
                raise UserError("Seules les idées en brouillon ou en cours peuvent être rejetées.")
            record.write({'statut': 'refusee'})
        return True
    
    def _creer_historique(self, ancien_statut, nouveau_statut):
        """Crée une entrée dans l'historique"""
        self.env['tp.idee.historique'].create({
            'idee_id': self.id,
            'ancien_statut': ancien_statut,
            'nouveau_statut': nouveau_statut,
            'user_id': self.env.user.id,
        })
    
    def _envoyer_notification(self, nouveau_statut):
        """Envoie une notification par email lors du changement de statut"""
        try:
            statut_labels = {
                "brouillon": "Brouillon",
                "en_cours": "En cours d'évaluation",
                "acceptee": "Acceptée",
                "refusee": "Refusée",
            }
            
            # Préparer les destinataires
            recipients = []
            if self.propose_par:
                # Essayer de trouver l'utilisateur par nom
                user = self.env['res.users'].search([('name', '=', self.propose_par)], limit=1)
                if user and user.email:
                    recipients.append(user.email)
            
            if self.responsable_id and self.responsable_id.email:
                if self.responsable_id.email not in recipients:
                    recipients.append(self.responsable_id.email)
            
            # Créer le message
            if recipients:
                subject = f"Changement de statut pour l'idée: {self.name}"
                body = f"""
                <p>Bonjour,</p>
                <p>Le statut de l'idée "<strong>{self.name}</strong>" a été modifié.</p>
                <p><strong>Nouveau statut:</strong> {statut_labels.get(nouveau_statut, nouveau_statut)}</p>
                <p><strong>Description:</strong> {self.description or 'Aucune description'}</p>
                <p>Cordialement,<br/>Système de Boîte à Idées</p>
                """
                
                # Utiliser mail.thread pour envoyer
                self.message_post(
                    subject=subject,
                    body=body,
                    email_to=','.join(recipients),
                    message_type='notification',
                )
        except Exception as e:
            # En cas d'erreur, on log mais on ne bloque pas le processus
            pass
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override pour créer l'historique initial et remplir propose_par"""
        # Remplir automatiquement propose_par si non spécifié
        for vals in vals_list:
            if 'propose_par' not in vals or not vals.get('propose_par'):
                vals['propose_par'] = self.env.user.name
        
        records = super(TpIdee, self).create(vals_list)
        for record in records:
            if record.statut:
                record.sudo()._creer_historique(False, record.statut)
        return records
    
    def write(self, vals):
        """Override pour créer l'historique lors du changement de statut et vérifier les permissions"""
        # Vérifier les permissions pour les employés : ils ne peuvent modifier que leurs propres idées
        if self.env.user.has_group('tp_boite_idees.group_tp_idee_user') and not self.env.user.has_group('tp_boite_idees.group_tp_idee_manager'):
            for record in self:
                if record.propose_par and record.propose_par != self.env.user.name:
                    raise UserError("Vous ne pouvez modifier que vos propres idées.")
        
        if 'statut' in vals:
            for record in self:
                ancien_statut = record.statut
                nouveau_statut = vals['statut']
                if ancien_statut != nouveau_statut:
                    result = super(TpIdee, record).write(vals)
                    # Utiliser sudo() pour éviter les problèmes de droits
                    record.sudo()._creer_historique(ancien_statut, nouveau_statut)
                    record.sudo()._envoyer_notification(nouveau_statut)
                    return result
        return super(TpIdee, self).write(vals)
