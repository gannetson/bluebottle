/*
 Include the JWT token in the header of all api requests.
 */
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (sameOrigin(settings.url) && App.get('jwtToken')) {
            // Send the token to same-origin, relative URLs only. 
            // Fetching JWT Token occurs during login.
            xhr.setRequestHeader("Authorization", "JWT " + App.get('jwtToken'));
        }
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", App.get('csrfToken'));
        }
    }
});

App.AuthJwt = {
    // Use this function to process the response containing a JWT token
    // It should be used with a promise and the response of the form:
    //    {token: '123abc'}
    processSuccessResponse: function (response, resolve) {
        // If resolve is not defined then resolve the promise
        // by returning the currentUser
        if (resolve === undefined) {
            resolve = function (value) {
                if (resolved) { return; }
                resolved = true;
                resolve(promise, value);
            };
        }

        // User authentication succeeded. Store the token:
        // 1) in the local store for use if the user reloads the page
        // 2) in a property on the App 
        localStorage['jwtToken'] = response.token;
        App.set('jwtToken', response.token);

        // In Ember Data < beta the App.CurrentUser gets stuck in the root.error
        // state so we need to force a transition here before trying to fetch the
        // user again.
        currentUser = App.CurrentUser.find('current');
        if (currentUser.get('currentState.error.stateName') == 'root.error') {
            currentUser.transitionTo('deleted.saved');
            currentUser = App.CurrentUser.find('current').then( function (user) {
                Ember.run(null, resolve, user);
            });
        } else {
            Ember.run(null, resolve, currentUser);
        }
    }
}

/*
 Ensure we reload the JWT token from the local store if possible.
 This needs to happen before the ember store loads so the api 
 requests can include the JWT token if available.
 */
// TODO: Enable this once we work out why we can't use the jwt token after
//       a reload. It seems it is only valid for one session??
// Ember.Application.initializer({
//     name: 'setJwtToken',
//     before: 'currentUser',
//     initialize: function(container, application) {
//         var jwtToken = localStorage['jwtToken'];
//         if (jwtToken)
//             App.set('jwtToken', jwtToken);
//     }
// });

/* 
 A mixin for JWT authentication - this will be called from the BB LoginController
 when the user submits the login (username/password) form. 
 */
App.AuthJwtMixin = Em.Mixin.create({
    authorizeUser: function (username, password) {
        var _this = this,
            username = _this.get('username'),
            password = _this.get('password');
        
        return Ember.RSVP.Promise(function (resolve, reject) {
            debugger
            var hash = {
              url: "/api/token-auth/",
              dataType: "json",
              type: 'post',
              data: {
                  username: username,
                  password: password
              }
            };
           
            hash.success = function (response) {
                App.AuthJwt.processSuccessResponse(response, resolve);
            };
           
            hash.error = function (response) {
                var error = JSON.parse(response.responseText);
                Ember.run(null, reject, error);
            };
           
            Ember.$.ajax(hash);
        });
    }
});

/*
 Custom logout action for JWT
 */
App.LogoutJwtMixin = Em.Mixin.create({
    actions: {
        logout: function () {
            // Clear the jwtToken references
            App.set('jwtToken', null);
            delete localStorage['jwtToken'];

            // Clear the current user details
            this.controllerFor('currentUser').set('model', null);

            // Redirect to?? If the user is in a restricted route then 
            // they should be redirected to the home route. For now we 
            // always force them to the home
            this.transitionTo('home');
        }
    },
});