/* Embedded objects */

App.Adapter.map('App.ProjectDonation', {
    user: {embedded: 'load'}
});

/* Models */

App.Donation = DS.Model.extend({
    amount: DS.attr('number', {defaultValue: 25}),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser'),
    user: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date')
});

App.ProjectDonation = DS.Model.extend({
    url: 'donations/project',

    amount: DS.attr('number'),
    created: DS.attr('date'),
    user: DS.belongsTo('App.UserPreview')
});

App.MyDonation = App.Donation.extend({
    url: 'donations/my',

    order: DS.belongsTo('App.MyOrder'),
    amount: DS.attr('number', {defaultValue: 25}),
    validAmount: Em.computed.gte('amount', 5)
});
