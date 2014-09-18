# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Editor.
"""
from nose.plugins.attrib import attr
from .test_studio_video_module import CMSVideoBaseTest


@attr('shard_2')
class VideoEditorTest(CMSVideoBaseTest):
    """
    CMS Video Editor Test Class
    """

    def setUp(self):
        super(VideoEditorTest, self).setUp()

    def _create_video_component(self, subtitles=False):
        """
        Create a video component and navigate to unit page

        Arguments:
            subtitles (bool): Upload subtitles or not

        """
        if subtitles:
            self.assets.append('subs_OEoXaMPEzfM.srt.sjson')

        self.navigate_to_course_unit()

    def test_default_settings(self):
        """
        Scenario: User can view Video metadata
        Given I have created a Video component
        And I edit the component
        Then I see the correct video settings and default values
        """
        self._create_video_component()
        self.edit_component()
        self.assertTrue(self.video.verify_settings())

    def test_modify_video_display_name(self):
        """
        Scenario: User can modify Video display name
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        Then I can modify video display name
        And my video display name change is persisted on save
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.set_field_value('Component Display Name', 'Transformers')
        self.save_unit_settings()
        self.edit_component()
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Component Display Name', 'Transformers'))

    def test_hidden_captions(self):
        """
        Scenario: Captions are hidden when "transcript display" is false
        Given I have created a Video component with subtitles
        And I have set "transcript display" to False
        Then when I view the video it does not show the captions
        """
        self._create_video_component(subtitles=True)
        # Prevent cookies from overriding course settings
        self.browser.delete_cookie('hide_captions')
        self.edit_component()
        self.open_advanced_tab()
        self.video.set_field_value('Show Transcript', 'False', 'select')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())

    def test_shown_captions(self):
        """
        Scenario: Captions are shown when "transcript display" is true
        Given I have created a Video component with subtitles
        And I have set "transcript display" to True
        Then when I view the video it does show the captions
        """
        self._create_video_component(subtitles=True)
        # Prevent cookies from overriding course settings
        self.browser.delete_cookie('hide_captions')
        self.edit_component()
        self.open_advanced_tab()
        self.video.set_field_value('Show Transcript', 'True', 'select')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())

    def test_translations_uploading(self):
        """
        Scenario: Translations uploading works correctly
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "chinese_transcripts.srt" for "zh" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "zh"
        And I upload transcript file "uk_transcripts.srt" for "uk" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And video language menu has "uk, zh" translations
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh'])
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.assertIn(unicode_text, self.video.captions_text)
        self.assertEqual(self.video.caption_languages.keys(), ['zh', 'uk'])

    def test_upload_large_transcript(self):
        """
        Scenario: User can upload transcript file with > 1mb size
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "1mb_transcripts.srt" for "uk" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('1mb_transcripts.srt', 'uk')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_lines())

    def test_translations_download_works_w_saving(self):
        """
        Scenario: Translations downloading works correctly w/ preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |zh       |chinese_transcripts.srt|
        And I save changes
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "uk, zh"
        And video language menu has "uk, zh" translations
        Then I can download transcript for "zh" language code, that contains text "好 各位同学"
        And I can download transcript for "uk" language code, that contains text "Привіт, edX вітає вас."
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh', 'uk'])
        self.assertEqual(self.video.caption_languages.keys(), ['zh', 'uk'])
        zh_unicode_text = "好 各位同学".decode('utf-8')
        self.assertTrue(self.video.download_translation('zh', zh_unicode_text))
        uk_unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertTrue(self.video.download_translation('uk', uk_unicode_text))

    def test_translations_download_works_wo_saving(self):
        """
        Scenario: Translations downloading works correctly w/o preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |zh       |chinese_transcripts.srt|
        Then I can download transcript for "zh" language code, that contains text "好 各位同学"
        And I can download transcript for "uk" language code, that contains text "Привіт, edX вітає вас."
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        zh_unicode_text = "好 各位同学".decode('utf-8')
        self.assertTrue(self.video.download_translation('zh', zh_unicode_text))
        uk_unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertTrue(self.video.download_translation('uk', uk_unicode_text))

    def test_translations_remove_works_w_saving(self):
        """
        Scenario: Translations removing works correctly w/ preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |zh       |chinese_transcripts.srt|
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        And video language menu has "uk, zh" translations
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "uk, zh"
        Then I remove translation for "uk" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "zh"
        Then I remove translation for "zh" language code
        And I save changes
        Then when I view the video it does not show the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.assertEqual(self.video.caption_languages.keys(), ['zh', 'uk'])
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh', 'uk'])
        self.video.remove_translation('uk')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh'])
        self.video.remove_translation('zh')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())

    def test_translations_remove_works_wo_saving(self):
        """
        Scenario: Translations removing works correctly w/o preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "uk_transcripts.srt" for "uk" language code
        And I see translations for "uk"
        Then I remove translation for "uk" language code
        And I save changes
        Then when I view the video it does not show the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.assertEqual(self.video.translations(), ['uk'])
        self.video.remove_translation('uk')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())

    def test_translations_clearing_works_w_saving(self):
        """
        Scenario: Translations clearing works correctly w/ preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |zh       |chinese_transcripts.srt|
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        And video language menu has "uk, zh" translations
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "uk, zh"
        And I click button "Clear"
        And I save changes
        Then when I view the video it does not show the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.assertEqual(self.video.caption_languages.keys(), ['zh', 'uk'])
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh', 'uk'])
        self.video.click_button('translations_clear')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())

    def test_translations_clearing_works_wo_saving(self):
        """
        Scenario: Translations clearing works correctly w/o preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |zh       |chinese_transcripts.srt|
        And I click button "Clear"
        And I save changes
        Then when I view the video it does not show the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.video.click_button('translations_clear')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())

    def test_cannot_upload_sjson_translation(self):
        """
        Scenario: User cannot upload translations in sjson format
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I click button "Add"
        And I choose "uk" language code
        And I try to upload transcript file "subs_OEoXaMPEzfM.srt.sjson"
        Then I see validation error "Only SRT files can be uploaded. Please select a file ending in .srt to upload."
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.click_button('translation_add')
        self.video.select_translation_language('uk')
        self.video.upload_asset('subs_OEoXaMPEzfM.srt.sjson', asset_type='transcript')
        error_msg = 'Only SRT files can be uploaded. Please select a file ending in .srt to upload.'
        self.assertEqual(self.video.upload_status_message, error_msg)

    def test_replace_translation_w_save(self):
        """
        Scenario: User can easy replace the translation by another one w/ preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "chinese_transcripts.srt" for "zh" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "zh"
        And I replace transcript file for "zh" language code by "uk_transcripts.srt"
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.assertEqual(self.video.translations(), ['zh'])
        self.video.replace_translation('zh', 'uk', 'uk_transcripts.srt')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)

    def test_replace_translation_wo_save(self):
        """
        Scenario: User can easy replace the translation by another one w/o preliminary saving
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "chinese_transcripts.srt" for "zh" language code
        And I see translations for "zh"
        And I replace transcript file for "zh" language code by "uk_transcripts.srt"
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.assertEqual(self.video.translations(), ['zh'])
        self.video.replace_translation('zh', 'uk', 'uk_transcripts.srt')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)

    def test_translation_upload_remove_upload(self):
        """
        Scenario: Upload "zh" file "A" -> Remove "zh" -> Upload "zh" file "B"
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "chinese_transcripts.srt" for "zh" language code
        And I see translations for "zh"
        Then I remove translation for "zh" language code
        And I upload transcript file "uk_transcripts.srt" for "zh" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('chinese_transcripts.srt', 'zh')
        self.assertEqual(self.video.translations(), ['zh'])
        self.video.remove_translation('zh')
        self.video.upload_translation('uk_transcripts.srt', 'zh')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)

    def test_select_language_twice(self):
        """
        Scenario: User cannot select the same language twice
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I click button "Add"
        And I choose "zh" language code
        And I click button "Add"
        Then I cannot choose "zh" language code
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.click_button('translation_add')
        self.video.select_translation_language('zh')
        self.video.click_button('translation_add')
        self.video.select_translation_language('zh')
        self.assertEqual(self.video.translations(), [u'zh', u''])

    def test_table_of_contents(self):
        """
        Scenario: User can see table of content at the first position
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript files:
          |lang_code|filename               |
          |uk       |uk_transcripts.srt     |
          |table    |chinese_transcripts.srt|
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And video language menu has "table, uk" translations
        And I see video language with code "table" at position "0"
        """
        self._create_video_component()
        self.edit_component()
        self.open_advanced_tab()
        self.video.upload_translation('uk_transcripts.srt', 'uk')
        self.video.upload_translation('chinese_transcripts.srt', 'table')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.assertEqual(self.video.caption_languages.keys(), [u'table', u'uk'])
        self.assertEqual(self.video.caption_languages.keys()[0], 'table')
