/*
*  Views
*/

App.SignupView = App.FormView.extend({

    submitAction: 'signup',

    firstName: gettext("First name"),
    surname: gettext("Surname"),
    emailText: gettext("Email address"),
    reenterEmail: gettext("Re-enter email address"),
    passwordText: gettext("Password")

});

App.UserModalView = App.FormView.extend({
    templateName: 'user_modal'
});

App.LoginView = App.FormView.extend({
    templateName: 'login',

    placeholderText: gettext("Email address"),
    passwordText: gettext("Password"),

    next: function() {
        return  String(window.location);
    }.property(),

    submitAction: 'login'
});

App.PasswordResetView = App.FormView.extend({
    clearForm: function () {
        var controller = this.get('controller');

        controller.set('new_password1', null);
        controller.set('new_password2', null);
        controller.set('error', null);
    }.on('willInsertElement'),

    submitAction: 'resetPassword',

    next: function() {
        return  String(window.location);
    }.property()
});

App.PasswordRequestView = App.FormView.extend({
    placeholderText: gettext("Email address"),
    submitAction: 'requestReset'
});


App.ItemSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick an item")
});

App.DisableAccountView = App.FormView.extend({
     templateName: 'disable'

});

