function l10n_es_pos_simplified_invoice_screens(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb,
    _t = instance.web._t;

    var round_pr = instance.web.round_precision

    module.ReceiptScreenWidget = module.ScreenWidget.extend({
        template: 'ReceiptScreenWidget',

        show_numpad:     false,
        show_leftpane:   false,

        show: function(){
            this._super();
            var self = this;

            var print_button = this.add_action_button({
                    label: _t('Print'),
                    icon: '/point_of_sale/static/src/img/icons/png48/printer.png',
                    click: function(){ self.print(); },
                });

            var finish_button = this.add_action_button({
                    label: _t('Next Order'),
                    icon: '/point_of_sale/static/src/img/icons/png48/go-next.png',
                    click: function() { self.finishOrder(); },
                });

            this.refresh();

            if (!this.pos.get('selectedOrder')._printed) {
                this.print();
            }

            //
            // The problem is that in chrome the print() is asynchronous and doesn't
            // execute until all rpc are finished. So it conflicts with the rpc used
            // to send the orders to the backend, and the user is able to go to the next
            // screen before the printing dialog is opened. The problem is that what's
            // printed is whatever is in the page when the dialog is opened and not when it's called,
            // and so you end up printing the product list instead of the receipt...
            //
            // Fixing this would need a re-architecturing
            // of the code to postpone sending of orders after printing.
            //
            // But since the print dialog also blocks the other asynchronous calls, the
            // button enabling in the setTimeout() is blocked until the printing dialog is
            // closed. But the timeout has to be big enough or else it doesn't work
            // 2 seconds is the same as the default timeout for sending orders and so the dialog
            // should have appeared before the timeout... so yeah that's not ultra reliable.

            finish_button.set_disabled(true);
            setTimeout(function(){
                finish_button.set_disabled(false);
            }, 2000);
        },
        print: function() {
            this.pos.get('selectedOrder')._printed = true;
            window.print();
        },
        finishOrder: function() {
            this.pos.get('selectedOrder').destroy();
        },
        refresh: function() {
            var order = this.pos.get('selectedOrder');
            $('.pos-receipt-container', this.$el).html(QWeb.render('PosTicket_l10n_es',{
                    widget:this,
                    order: order,
                    orderlines: order.get('orderLines').models,
                    paymentlines: order.get('paymentLines').models,
                }));
        },
        close: function(){
            this._super();
        }
    });

    module.ClientListScreenWidget = module.ScreenWidget.extend({
        template: 'ClientListScreenWidget',

        init: function(parent, options){
            this._super(parent, options);
        },

        show_leftpane: false,

        auto_back: true,

        show: function(){
            var self = this;
            this._super();

            this.renderElement();
            this.details_visible = false;
            this.old_client = this.pos.get('selectedOrder').get('client');
            this.new_client = this.old_client;

            this.$('.back').click(function(){
                self.pos_widget.screen_selector.back();
            });

            this.$('.next').click(function(){
                self.save_changes();
                self.pos_widget.screen_selector.back();
            });

            this.$('.new-customer').click(function(){
                self.display_client_details('edit',{
                    'country_id': self.pos.company.country_id,
                });
            });

            var partners = this.pos.db.get_partners_sorted(1000);
            this.render_list(partners);

            this.reload_partners();

            if( this.old_client ){
                this.display_client_details('show',this.old_client,0);
            }

            this.$('.client-list-contents').delegate('.client-line','click',function(event){
                self.line_select(event,$(this),parseInt($(this).data('id')));
            });

            var search_timeout = null;

            if(this.pos.config.iface_vkeyboard && this.pos_widget.onscreen_keyboard){
                this.pos_widget.onscreen_keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);

                var query = this.value;

                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
        },
        barcode_client_action: function(code){
            if (this.editing_client) {
                this.$('.detail.barcode').val(code.code);
            } else if (this.pos.db.get_partner_by_ean13(code.code)) {
                this.display_client_details('show',this.pos.db.get_partner_by_ean13(code.code));
            }
        },
        perform_search: function(query, associate_result){
            if(query){
                var customers = this.pos.db.search_partner(query);
                this.display_client_details('hide');
                if ( associate_result && customers.length === 1){
                    this.new_client = customers[0];
                    this.save_changes();
                    this.pos_widget.screen_selector.back();
                }
                this.render_list(customers);
            }else{
                var customers = this.pos.db.get_partners_sorted();
                this.render_list(customers);
            }
        },
        clear_search: function(){
            var customers = this.pos.db.get_partners_sorted(1000);
            this.render_list(customers);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
        render_list: function(partners){
            var contents = this.$el[0].querySelector('.client-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(partners.length,1000); i < len; i++){
                var partner    = partners[i];
                var clientline_html = QWeb.render('ClientLine',{widget: this, partner:partners[i]});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];

                if( partners === this.new_client ){
                    clientline.classList.add('highlight');
                }else{
                    clientline.classList.remove('highlight');
                }

                contents.appendChild(clientline);
            }
        },
        save_changes: function(){
            if( this.has_client_changed() ){
                this.pos.get('selectedOrder').set_client(this.new_client);
            }
        },
        has_client_changed: function(){
            if( this.old_client && this.new_client ){
                return this.old_client.id !== this.new_client.id;
            }else{
                return !!this.old_client !== !!this.new_client;
            }
        },
        toggle_save_button: function(){
            var $button = this.$('.button.next');
            if (this.editing_client) {
                $button.addClass('oe_hidden');
                return;
            } else if( this.new_client ){
                if( !this.old_client){
                    $button.text(_t('Set Customer'));
                }else{
                    $button.text(_t('Change Customer'));
                }
            }else{
                $button.text(_t('Deselect Customer'));
            }
            $button.toggleClass('oe_hidden',!this.has_client_changed());
        },
        line_select: function(event,$line,id){
            var partner = this.pos.db.get_partner_by_id(id);
            this.$('.client-list .lowlight').removeClass('lowlight');
            if ( $line.hasClass('highlight') ){
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_client_details('hide',partner);
                this.new_client = null;
                this.toggle_save_button();
            }else{
                this.$('.client-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                var y = event.pageY - $line.parent().offset().top
                this.display_client_details('show',partner,y);
                this.new_client = partner;
                this.toggle_save_button();
            }
        },
        partner_icon_url: function(id){
            return '/web/binary/image?model=res.partner&id='+id+'&field=image_small';
        },

        // ui handle for the 'edit selected customer' action
        edit_client_details: function(partner) {
            this.display_client_details('edit',partner);
        },

        // ui handle for the 'cancel customer edit changes' action
        undo_client_details: function(partner) {
            if (!partner.id) {
                this.display_client_details('hide');
            } else {
                this.display_client_details('show',partner);
            }
        },

        // what happens when we save the changes on the client edit form -> we fetch the fields, sanitize them,
        // send them to the backend for update, and call saved_client_details() when the server tells us the
        // save was successfull.
        save_client_details: function(partner) {
            var self = this;

            var fields = {}
            this.$('.client-details-contents .detail').each(function(idx,el){
                fields[el.name] = el.value;
            });

            if (!fields.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('A Customer Name Is Required'),
                });
                return;
            }

            if (this.uploaded_picture) {
                fields.image = this.uploaded_picture;
            }

            fields.id           = partner.id || false;
            fields.country_id   = fields.country_id || false;
            fields.ean13        = fields.ean13 ? this.pos.barcode_reader.sanitize_ean(fields.ean13) : false;

            new instance.web.Model('res.partner').call('create_from_ui',[fields]).then(function(partner_id){
                self.saved_client_details(partner_id);
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: Could not Save Changes'),
                    'comment':_t('Your Internet connection is probably down.'),
                });
            });
        },

        // what happens when we've just pushed modifications for a partner of id partner_id
        saved_client_details: function(partner_id){
            var self = this;
            this.reload_partners().then(function(){
                var partner = self.pos.db.get_partner_by_id(partner_id);
                if (partner) {
                    self.new_client = partner;
                    self.toggle_save_button();
                    self.display_client_details('show',partner);
                } else {
                    // should never happen, because create_from_ui must return the id of the partner it
                    // has created, and reload_partner() must have loaded the newly created partner.
                    self.display_client_details('hide');
                }
            });
        },

        // resizes an image, keeping the aspect ratio intact,
        // the resize is useful to avoid sending 12Mpixels jpegs
        // over a wireless connection.
        resize_image_to_dataurl: function(img, maxwidth, maxheight, callback){
            img.onload = function(){
                var png = new Image();
                var canvas = document.createElement('canvas');
                var ctx    = canvas.getContext('2d');
                var ratio  = 1;

                if (img.width > maxwidth) {
                    ratio = maxwidth / img.width;
                }
                if (img.height * ratio > maxheight) {
                    ratio = maxheight / img.height;
                }
                var width  = Math.floor(img.width * ratio);
                var height = Math.floor(img.height * ratio);

                canvas.width  = width;
                canvas.height = height;
                ctx.drawImage(img,0,0,width,height);

                var dataurl = canvas.toDataURL();
                callback(dataurl);
            }
        },

        // Loads and resizes a File that contains an image.
        // callback gets a dataurl in case of success.
        load_image_file: function(file, callback){
            var self = this;
            if (!file.type.match(/image.*/)) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message:_t('Unsupported File Format'),
                    comment:_t('Only web-compatible Image formats such as .png or .jpeg are supported'),
                });
                return;
            }

            var reader = new FileReader();
            reader.onload = function(event){
                var dataurl = event.target.result;
                var img     = new Image();
                img.src = dataurl;
                self.resize_image_to_dataurl(img,800,600,callback);
            }
            reader.onerror = function(){
                self.pos_widget.screen_selector.show_popup('error',{
                    message:_t('Could Not Read Image'),
                    comment:_t('The provided file could not be read due to an unknown error'),
                });
            };
            reader.readAsDataURL(file);
        },

        // This fetches partner changes on the server, and in case of changes,
        // rerenders the affected views
        reload_partners: function(){
            var self = this;
            return this.pos.load_new_partners().then(function(){
                self.render_list(self.pos.db.get_partners_sorted(1000));

                // update the currently assigned client if it has been changed in db.
                var curr_client = self.pos.get_order().get_client();
                if (curr_client) {
                    self.pos.get_order().set_client(self.pos.db.get_partner_by_id(curr_client.id));
                }
            });
        },

        // Shows,hides or edit the customer details box :
        // visibility: 'show', 'hide' or 'edit'
        // partner:    the partner object to show or edit
        // clickpos:   the height of the click on the list (in pixel), used
        //             to maintain consistent scroll.
        display_client_details: function(visibility,partner,clickpos){
            var self = this;
            var contents = this.$('.client-details-contents');
            var parent   = this.$('.client-list').parent();
            var scroll   = parent.scrollTop();
            var height   = contents.height();

            contents.off('click','.button.edit');
            contents.off('click','.button.save');
            contents.off('click','.button.undo');
            contents.on('click','.button.edit',function(){ self.edit_client_details(partner); });
            contents.on('click','.button.save',function(){ self.save_client_details(partner); });
            contents.on('click','.button.undo',function(){ self.undo_client_details(partner); });
            this.editing_client = false;
            this.uploaded_picture = null;

            if(visibility === 'show'){
                contents.empty();
                contents.append($(QWeb.render('ClientDetails',{widget:this,partner:partner})));

                var new_height   = contents.height();

                if(!this.details_visible){
                    if(clickpos < scroll + new_height + 20 ){
                        parent.scrollTop( clickpos - 20 );
                    }else{
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                }else{
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }

                this.details_visible = true;
                this.toggle_save_button();
            } else if (visibility === 'edit') {
                this.editing_client = true;
                contents.empty();
                contents.append($(QWeb.render('ClientDetailsEdit_l10n_es',{widget:this,partner:partner})));
                this.toggle_save_button();

                contents.find('.image-uploader').on('change',function(){
                    self.load_image_file(event.target.files[0],function(res){
                        if (res) {
                            contents.find('.client-picture img, .client-picture .fa').remove();
                            contents.find('.client-picture').append("<img src='"+res+"'>");
                            contents.find('.detail.picture').remove();
                            self.uploaded_picture = res;
                        }
                    });
                });
            } else if (visibility === 'hide') {
                contents.empty();
                if( height > scroll ){
                    contents.css({height:height+'px'});
                    contents.animate({height:0},400,function(){
                        contents.css({height:''});
                    });
                }else{
                    parent.scrollTop( parent.scrollTop() - height);
                }
                this.details_visible = false;
                this.toggle_save_button();
            }
        },
        close: function(){
            this._super();
        },
    });

    module.PaymentScreenWidget = module.ScreenWidget.extend({
        template: 'PaymentScreenWidget',
        back_screen: 'products',
        next_screen: 'receipt',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);

            this.pos.bind('change:selectedOrder',function(){
                    this.bind_events();
                    this.renderElement();
                },this);

            this.bind_events();

            this.line_delete_handler = function(event){
                var node = this;
                while(node && !node.classList.contains('paymentline')){
                    node = node.parentNode;
                }
                if(node){
                    self.pos.get('selectedOrder').removePaymentline(node.line)
                }
                event.stopPropagation();
            };

            this.line_change_handler = function(event){
                var node = this;
                while(node && !node.classList.contains('paymentline')){
                    node = node.parentNode;
                }
                if(node){
                    node.line.set_amount(this.value);
                }
            };

            this.line_click_handler = function(event){
                var node = this;
                while(node && !node.classList.contains('paymentline')){
                    node = node.parentNode;
                }
                if(node){
                    self.pos.get('selectedOrder').selectPaymentline(node.line);
                }
            };

            this.hotkey_handler = function(event){
                if(event.which === 13){
                    self.validate_order();
                }else if(event.which === 27){
                    self.back();
                }
            };

        },
        show: function(){
            this._super();
            var self = this;

            this.enable_numpad();
            this.focus_selected_line();

            document.body.addEventListener('keyup', this.hotkey_handler);

            this.add_action_button({
                    label: _t('Back'),
                    icon: '/point_of_sale/static/src/img/icons/png48/go-previous.png',
                    click: function(){
                        self.back();
                    },
                });

            this.add_action_button({
                    label: _t('Validate'),
                    name: 'validation',
                    icon: '/point_of_sale/static/src/img/icons/png48/validate.png',
                    click: function(){
                        self.validate_order();
                    },
                });

            if( this.pos.config.iface_invoicing ){
                this.add_action_button({
                        label: _t('Invoice'),
                        name: 'invoice',
                        icon: '/point_of_sale/static/src/img/icons/png48/invoice.png',
                        click: function(){
                            self.validate_order({invoice: true});
                        },
                    });
            }

            if( this.pos.config.iface_cashdrawer ){
                this.add_action_button({
                        label: _t('Cash'),
                        name: 'cashbox',
                        icon: '/point_of_sale/static/src/img/open-cashbox.png',
                        click: function(){
                            self.pos.proxy.open_cashbox();
                        },
                    });
            }

            this.update_payment_summary();

        },
        close: function(){
            this._super();
            this.disable_numpad();
            document.body.removeEventListener('keyup',this.hotkey_handler);
        },
        remove_empty_lines: function(){
            var order = this.pos.get('selectedOrder');
            var lines = order.get('paymentLines').models.slice(0);
            for(var i = 0; i < lines.length; i++){
                var line = lines[i];
                if(line.get_amount() === 0){
                    order.removePaymentline(line);
                }
            }
        },
        back: function() {
            this.remove_empty_lines();
            this.pos_widget.screen_selector.set_current_screen(this.back_screen);
        },
        bind_events: function() {
            if(this.old_order){
                this.old_order.unbind(null,null,this);
            }
            var order = this.pos.get('selectedOrder');
                order.bind('change:selected_paymentline',this.focus_selected_line,this);

            this.old_order = order;

            if(this.old_paymentlines){
                this.old_paymentlines.unbind(null,null,this);
            }
            var paymentlines = order.get('paymentLines');
                paymentlines.bind('add', this.add_paymentline, this);
                paymentlines.bind('change:selected', this.rerender_paymentline, this);
                paymentlines.bind('change:amount', function(line){
                        if(!line.selected && line.node){
                            line.node.value = line.amount.toFixed(this.pos.currency.decimals);
                        }
                        this.update_payment_summary();
                    },this);
                paymentlines.bind('remove', this.remove_paymentline, this);
                paymentlines.bind('all', this.update_payment_summary, this);

            this.old_paymentlines = paymentlines;

            if(this.old_orderlines){
                this.old_orderlines.unbind(null,null,this);
            }
            var orderlines = order.get('orderLines');
                orderlines.bind('all', this.update_payment_summary, this);

            this.old_orderlines = orderlines;
        },
        focus_selected_line: function(){
            var line = this.pos.get('selectedOrder').selected_paymentline;
            if(line){
                var input = line.node.querySelector('input');
                if(!input){
                    return;
                }
                var value = input.value;
                input.focus();

                if(this.numpad_state){
                    this.numpad_state.reset();
                }

                if(Number(value) === 0){
                    input.value = '';
                }else{
                    input.value = value;
                    input.select();
                }
            }
        },
        add_paymentline: function(line) {
            var list_container = this.el.querySelector('.payment-lines');
                list_container.appendChild(this.render_paymentline(line));

            if(this.numpad_state){
                this.numpad_state.reset();
            }
        },
        render_paymentline: function(line){
            var el_html  = openerp.qweb.render('Paymentline',{widget: this, line: line});
                el_html  = _.str.trim(el_html);

            var el_node  = document.createElement('tbody');
                el_node.innerHTML = el_html;
                el_node = el_node.childNodes[0];
                el_node.line = line;
                el_node.querySelector('.paymentline-delete')
                    .addEventListener('click', this.line_delete_handler);
                el_node.addEventListener('click', this.line_click_handler);
                el_node.querySelector('input')
                    .addEventListener('keyup', this.line_change_handler);

            line.node = el_node;

            return el_node;
        },
        rerender_paymentline: function(line){
            var old_node = line.node;
            var new_node = this.render_paymentline(line);

            old_node.parentNode.replaceChild(new_node,old_node);
        },
        remove_paymentline: function(line){
            line.node.parentNode.removeChild(line.node);
            line.node = undefined;
        },
        renderElement: function(){
            this._super();

            var paymentlines   = this.pos.get('selectedOrder').get('paymentLines').models;
            var list_container = this.el.querySelector('.payment-lines');

            for(var i = 0; i < paymentlines.length; i++){
                list_container.appendChild(this.render_paymentline(paymentlines[i]));
            }

            this.update_payment_summary();
        },
        update_payment_summary: function() {
            var currentOrder = this.pos.get('selectedOrder');
            var paidTotal = currentOrder.getPaidTotal();
            var dueTotal = currentOrder.getTotalTaxIncluded();
            var remaining = dueTotal > paidTotal ? dueTotal - paidTotal : 0;
            var change = paidTotal > dueTotal ? paidTotal - dueTotal : 0;

            this.$('.payment-due-total').html(this.format_currency(dueTotal));
            this.$('.payment-paid-total').html(this.format_currency(paidTotal));
            this.$('.payment-remaining').html(this.format_currency(remaining));
            this.$('.payment-change').html(this.format_currency(change));
            if(currentOrder.selected_orderline === undefined){
                remaining = 1;  // What is this ?
            }

            if(this.pos_widget.action_bar){
                if (dueTotal <= 400){
                    this.pos_widget.action_bar.set_button_disabled('validation', !this.is_paid());
                }else{
                    this.pos_widget.action_bar.set_button_disabled('validation', true);
                }
                this.pos_widget.action_bar.set_button_disabled('invoice', !this.is_paid());
            }
        },
        is_paid: function(){
            var currentOrder = this.pos.get('selectedOrder');
            return (currentOrder.getTotalTaxIncluded() < 0.000001
                   || currentOrder.getPaidTotal() + 0.000001 >= currentOrder.getTotalTaxIncluded());

        },
        validate_order: function(options) {
            var self = this;
            options = options || {};

            var currentOrder = this.pos.get('selectedOrder');

            if(currentOrder.get('orderLines').models.length === 0){
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Empty Order'),
                    'comment': _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = currentOrder.get('paymentLines').models;
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }

            if(!this.is_paid()){
                return;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(currentOrder.getTotalTaxIncluded() - currentOrder.getPaidTotal()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        message: _t('Cannot return change without a cash payment method'),
                        comment: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            if (this.pos.config.iface_cashdrawer) {
                    this.pos.proxy.open_cashbox();
            }

            if(options.invoice){
                // deactivate the validation button while we try to send the order
                this.pos_widget.action_bar.set_button_disabled('validation',true);
                this.pos_widget.action_bar.set_button_disabled('invoice',true);

                var invoiced = this.pos.push_and_invoice_order(currentOrder);
                var dueTotal = currentOrder.getTotalTaxIncluded();

                invoiced.fail(function(error){
                    if(error === 'error-no-client'){
                        self.pos_widget.screen_selector.show_popup('error',{
                            message: _t('An anonymous order cannot be invoiced'),
                            comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                        });
                    }else{
                        self.pos_widget.screen_selector.show_popup('error',{
                            message: _t('The order could not be sent'),
                            comment: _t('Check your internet connection and try again.'),
                        });
                    }
                    if (dueTotal <= 400){
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                    }else{
                        self.pos_widget.action_bar.set_button_disabled('validation',true);
                    }
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                });

                invoiced.done(function(){
                    if (dueTotal <= 400){
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                    }else{
                        self.pos_widget.action_bar.set_button_disabled('validation',true);
                    }
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    self.pos.get('selectedOrder').destroy();
                });

            }else{
                this.pos.push_order(currentOrder)
                if(this.pos.config.iface_print_via_proxy){
                    var receipt = currentOrder.export_for_printing();
                    this.pos.proxy.print_receipt(QWeb.render('XmlReceipt',{
                        receipt: receipt, widget: self,
                    }));
                    this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                }else{
                    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                }
            }

            // hide onscreen (iOS) keyboard
            setTimeout(function(){
                document.activeElement.blur();
                $("input").blur();
            },250);
        },
        enable_numpad: function(){
            this.disable_numpad();  //ensure we don't register the callbacks twice
            this.numpad_state = this.pos_widget.numpad.state;
            if(this.numpad_state){
                this.numpad_state.reset();
                this.numpad_state.changeMode('payment');
                this.numpad_state.bind('set_value',   this.set_value, this);
                this.numpad_state.bind('change:mode', this.set_mode_back_to_payment, this);
            }

        },
        disable_numpad: function(){
            if(this.numpad_state){
                this.numpad_state.unbind('set_value',  this.set_value);
                this.numpad_state.unbind('change:mode',this.set_mode_back_to_payment);
            }
        },
        set_mode_back_to_payment: function() {
            this.numpad_state.set({mode: 'payment'});
        },
        set_value: function(val) {
            var selected_line =this.pos.get('selectedOrder').selected_paymentline;
            if(selected_line){
                selected_line.set_amount(val);
                selected_line.node.querySelector('input').value = selected_line.amount.toFixed(2);
            }
        },
    });

}
