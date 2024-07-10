odoo.define("website_sale_cart_expire", (require) => {
    "use strict";

    const publicWidget = require("web.public.widget");
    const time = require("web.time");

    /**
     * Widget del Temporizador de Expiración del Carrito.
     *
     * Muestra un temporizador de cuenta regresiva para la fecha de expiración del carrito.
     */
    publicWidget.registry.WebsiteSaleCartExpireTimer = publicWidget.Widget.extend({
        selector: ".my_cart_expiration",

        /**
         * @override
         */
        start: async function () {
            await this._super.apply(this, arguments);
            this._setExpirationDate(this.$el.data("order-expire-date"));
            const remainingMs = this._getRemainingMs();
            if (remainingMs > 0) {
                this._renderTimer(remainingMs);
                this._startTimer();
            }
            // Intenta conectarse al widget de cantidad del carrito para actualizar la fecha de expiración
            // siempre que cambie.
            this.$el.siblings(".my_cart_quantity").on(
                "DOMSubtreeModified",
                _.debounce(() => this._refreshExpirationDate(), 250)
            );
        },
        /**
         * @override
         */
        destroy: function () {
            this.$el.remove();
            this._stopTimer();
            return this._super.apply(this, arguments);
        },
        /**
         * Establece la fecha objetivo del temporizador.
         *
         * @param {String|Date} expireDate
         */
        _setExpirationDate: function (expireDate) {
            if (typeof expireDate === "string") {
                expireDate = time.str_to_datetime(expireDate);
            }
            this.expireDate = expireDate ? moment(expireDate) : false;
        },
        /**
         * @returns {Number}
         */
        _getRemainingMs: function () {
            return this.expireDate ? this.expireDate.diff(moment()) : 0;
        },
        /**
         * Inicia el temporizador.
         */
        _startTimer: function () {
            this._stopTimer();
            this.timer = setInterval(this._refreshTimer.bind(this), 1000);
        },
        /**
         * Detiene el temporizador.
         */
        _stopTimer: function () {
            if (this.timer) {
                clearInterval(this.timer);
            }
        },
        /**
         * Refresca el temporizador de cuenta regresiva.
         * Se destruye a sí mismo si la cuenta regresiva llega a 0.
         */
        _refreshTimer: function () {
            const remainingMs = this._getRemainingMs();
            this._renderTimer(remainingMs);
            if (remainingMs <= 0) {
                this._stopTimer();
                this._refreshExpirationDate();
            }
        },
        /**
         * Actualiza el tiempo restante en el DOM
         */
        _renderTimer: function (remainingMs) {
            const remainingMsRounded = Math.ceil(remainingMs / 1000) * 1000;
            // No mostrar el temporizador si el tiempo restante es menor a 1 hora
            if (remainingMsRounded >= 3600000) {
                return this.$el.hide();
            }
            this.$el.show();
            // Formatear el temporizador de cuenta regresiva
            const remainingStr = moment.utc(remainingMsRounded).format("mm:ss");
            if (remainingStr !== this.$el.text()) {
                this.$el.text(remainingStr);
            }
        },
        /**
         * Actualiza la fecha de expiración leyendo desde el backend
         */
        _refreshExpirationDate: async function () {
            const expireDate = await this._rpc({route: "/shop/cart/get_expire_date"});
            this._setExpirationDate(expireDate);
            const remainingMs = this._getRemainingMs();
            if (remainingMs > 0) {
                this._renderTimer(remainingMs);
                this._startTimer();
                this.$el.show();
            } else {
                this._stopTimer();
                this.$el.hide();
            }
            return this.expireDate;
        },
    });
});
