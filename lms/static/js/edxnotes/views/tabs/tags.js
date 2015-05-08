;(function (define, undefined) {
'use strict';
define([
    'gettext', 'jquery', 'underscore', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
    'js/edxnotes/views/tab_view'
], function (gettext, $, _, NoteGroupView, TabPanelView, TabView) {

    var TagsView = TabView.extend({
        scrollToTag: function(tagName) {
            var titleElement;
            if (!this.tabModel.isActive()) {
                this.tabModel.activate();
            }
            titleElement = this.$el.find('.tags-title').filter(
                // Since tags can only be single words, we are safe just looking for the title
                // containing the tagName, and we don't need to worry about the display of the count.
                function(){ return $(this).text().indexOf(tagName.toLowerCase()) !== -1; }
            );
            $('html,body').animate({
                scrollTop: titleElement.offset().top - 10
            },'slow');
        },
        PanelConstructor: TabPanelView.extend({
            id: 'tags-panel',
            title: 'Tags',
            noTags: gettext('[no tags]'),  // User-defined tags cannot have spaces, so no risk of a collision.

            renderContent: function () {
                var notesByTag = {}, noTags = this.noTags, addNoteForTag, noteList, tags, i,
                    sortedTagNames, container, group, noteGroup;

                // Iterate through all the notes and build up a dictionary structure by tag.
                // Note that the collection will be in most-recently updated order already.
                addNoteForTag = function (note, tag) {
                    noteList = notesByTag[tag.toLowerCase()];
                    if (noteList === undefined) {
                        noteList = [];
                        notesByTag[tag.toLowerCase()] = noteList;
                    }
                    // If a note was tagged with the same tag more than once, don't add again.
                    // We can assume it would be the last element of the list because we iterate through
                    // all tags on a given note before moving on to the text note.
                    if (noteList.length === 0 || noteList[noteList.length -1] !== note) {
                        noteList.push(note);
                    }
                };

                this.collection.each(function(note){
                    tags = note.get('tags');
                    if (tags.length === 0) {
                        addNoteForTag(note, noTags);
                    }
                    else {
                        for (i = 0; i < tags.length; i++) {
                            addNoteForTag(note, tags[i]);
                        }
                    }
                });

                sortedTagNames = Object.keys(notesByTag).sort(function (a, b) {
                    // "no tags" should always appear last
                    if (a === noTags) {
                        return 1;
                    }
                    else if (b === noTags) {
                        return -1;
                    }
                    else if (notesByTag[a].length > notesByTag[b].length) {
                        return -1;
                    }
                    else if (notesByTag[a].length < notesByTag[b].length) {
                        return 1;
                    }
                    else {
                        return a.toLowerCase() <= b.toLowerCase() ? -1 : 1;
                    }
                });

               container = document.createDocumentFragment();

                _.each(sortedTagNames, function (tagName) {
                    noteGroup = notesByTag[tagName];
                    group = this.getGroup(
                        interpolate_text(
                            gettext("{tagName} ({numberOfNotesWithTag})"),
                            {tagName: tagName, numberOfNotesWithTag: noteGroup.length}
                        )
                    );
                    group.addChild(this.getNotes(noteGroup));
                    container.appendChild(group.render().el);
                }, this);

                this.$el.append(container);
                return this;
            },

            getGroup: function (tagName) {
                var group = new NoteGroupView.GroupView({
                    displayName: tagName,
                    template: '<h3 class="tags-title"><%- displayName %></h3>',
                    className: "note-group"
                });
                this.children.push(group);
                return group;
            }
        }),

        tabInfo: {
            name: gettext('Tags'),
            identifier: 'view-tags',
            icon: 'fa fa-tag'
        }
    });

    return TagsView;
});
}).call(this, define || RequireJS.define);
