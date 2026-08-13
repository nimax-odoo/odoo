import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.portalDetailsapp = publicWidget.Widget.extend({
    selector: '.formulario_acces',
    events: {
        'click .cklickeame': '_onClickAllow',
        'change #vat': '_onChangevat',
    },
    
    init() {
        this._super(...arguments);
        // this.orm = useService('orm');
        // this.notification = this.bindService("notification");
    },

    /**
     * Will start the timer to display the notification request popup.
     *
     * Also pushes down the notification window if the main menu nav bar is active.
     * (We want to avoid covering the nav bar with the notification window)
     *
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments);
    },

    _onClickAllow: function () {
        console.log('clickame');
        alert("clickame");
    },
    _onChangevat: function () {
        var vat = document.querySelector("#vat").value;
        console.log(vat);
            return rpc("/access_successful/partner", {
                'vat': vat
            }).then(function (data){
                console.log(data);
                window.test = data;
                document.querySelector("#name").value = data.partner.name;
                document.querySelector("#email").value = data.partner.email;

            });
    },




});

// export default login_successful;
