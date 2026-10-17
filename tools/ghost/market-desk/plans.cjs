'use strict';
// Display prices only. No paid entitlements exist until billing is activated.
const PLANS=Object.freeze([
 Object.freeze({id:'public',name:'Public',monthlyCents:0,currency:'USD',available:true}),
 Object.freeze({id:'member',name:'Member',monthlyCents:999,currency:'USD',available:false}),
 Object.freeze({id:'executive',name:'Executive',monthlyCents:9900,currency:'USD',available:false})
]);
module.exports={PLANS};
