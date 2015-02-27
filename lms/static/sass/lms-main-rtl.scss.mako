## Note: This Sass infrastructure is repeated in application-extend1 and application-extend2, but needed in order to address an IE9 rule limit within CSS - http://blogs.msdn.com/b/ieinternals/archive/2011/05/14/10164546.aspx

// lms - css application architecture
// ====================

// libs and resets *do not edit*
@import 'vendor/bourbon/bourbon'; // lib - bourbon
@import 'vendor/bi-app/bi-app-rtl'; // set the layout for left to right languages

@import 'build';
