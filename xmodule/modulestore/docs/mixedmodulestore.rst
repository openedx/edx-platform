#################
MixedModuleStore
#################

MixedModuleStore provides a common API for all modulestore functions.

In addition, MixedModuleStore allows you to select which modulestore a
specific course is stored in (XMLModuleStore, DraftModuleStore, Split Mongo)
and routes requests for that course to the correct modulestore.

MixedModuleStore can also handle some conversions from one modulestore to
another.