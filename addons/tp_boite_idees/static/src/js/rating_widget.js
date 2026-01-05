odoo.define('tp_boite_idees.rating_widget', function (require) {
    'use strict';

    var FieldInteger = require('web.basic_fields').FieldInteger;
    var registry = require('web.field_registry');

    var RatingWidget = FieldInteger.extend({
        _render: function () {
            this._super.apply(this, arguments);
            if (this.mode === 'readonly') {
                var value = this.value || 0;
                var stars = '';
                for (var i = 1; i <= 5; i++) {
                    if (i <= value) {
                        stars += '<span class="fa fa-star text-warning"></span>';
                    } else {
                        stars += '<span class="fa fa-star-o text-muted"></span>';
                    }
                }
                this.$el.html(stars);
            } else {
                // En mode édition, utiliser un select simple
                var $select = $('<select class="form-control"/>');
                $select.append($('<option/>').attr('value', '0').text('0 étoiles'));
                for (var i = 1; i <= 5; i++) {
                    var option = $('<option/>').attr('value', i).text(i + ' étoile' + (i > 1 ? 's' : ''));
                    if (this.value == i) {
                        option.attr('selected', true);
                    }
                    $select.append(option);
                }
                this.$el.html($select);
                var self = this;
                $select.on('change', function() {
                    self._setValue(parseInt($(this).val()));
                });
            }
        },
    });

    registry.add('rating', RatingWidget);

    return RatingWidget;
});

