
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_bda51c3c` (`group_id`),
  KEY `auth_group_permissions_1e014c8f` (`permission_id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `permission_id_refs_id_a7792de1` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=238 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_registration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_registration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `activation_key` (`activation_key`),
  CONSTRAINT `user_id_refs_id_3fe8066a03e5b0b5` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_fbfc09f1` (`user_id`),
  KEY `auth_user_groups_bda51c3c` (`group_id`),
  CONSTRAINT `user_id_refs_id_831107f1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `group_id_refs_id_f0ee9890` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_fbfc09f1` (`user_id`),
  KEY `auth_user_user_permissions_1e014c8f` (`permission_id`),
  CONSTRAINT `user_id_refs_id_f2045483` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_userprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `language` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `meta` longtext NOT NULL,
  `courseware` varchar(255) NOT NULL,
  `gender` varchar(6) DEFAULT NULL,
  `mailing_address` longtext,
  `year_of_birth` int(11) DEFAULT NULL,
  `level_of_education` varchar(6) DEFAULT NULL,
  `goals` longtext,
  `allow_certificate` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `auth_userprofile_52094d6e` (`name`),
  KEY `auth_userprofile_8a7ac9ab` (`language`),
  KEY `auth_userprofile_b54954de` (`location`),
  KEY `auth_userprofile_fca3d292` (`gender`),
  KEY `auth_userprofile_d85587` (`year_of_birth`),
  KEY `auth_userprofile_551e365c` (`level_of_education`),
  CONSTRAINT `user_id_refs_id_3daaa960628b4c11` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_courseauthorization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_courseauthorization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `email_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `bulk_email_courseauthorization_ff48d8e5` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_courseemail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_courseemail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) DEFAULT NULL,
  `slug` varchar(128) NOT NULL,
  `subject` varchar(128) NOT NULL,
  `html_message` longtext,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `to_option` varchar(64) NOT NULL,
  `text_message` longtext,
  PRIMARY KEY (`id`),
  KEY `bulk_email_courseemail_901f59e9` (`sender_id`),
  KEY `bulk_email_courseemail_36af87d1` (`slug`),
  KEY `bulk_email_courseemail_ff48d8e5` (`course_id`),
  CONSTRAINT `sender_id_refs_id_5e8b8f9870ed6279` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_courseemailtemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_courseemailtemplate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `html_template` longtext,
  `plain_template` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_optout`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_optout` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bulk_email_optout_course_id_368f7519b2997e1a_uniq` (`course_id`,`user_id`),
  KEY `bulk_email_optout_ff48d8e5` (`course_id`),
  KEY `bulk_email_optout_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_fc2bac99e68e67c` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `celery_taskmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `result` longtext,
  `date_done` datetime NOT NULL,
  `traceback` longtext,
  `hidden` tinyint(1) NOT NULL,
  `meta` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `celery_taskmeta_c91f1bf` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(255) NOT NULL,
  `result` longtext NOT NULL,
  `date_done` datetime NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`),
  KEY `celery_tasksetmeta_c91f1bf` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificatewhitelist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificatewhitelist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `whitelist` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_certificatewhitelist_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_517c1c6aa7ba9306` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_generatedcertificate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_generatedcertificate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `download_url` varchar(128) NOT NULL,
  `grade` varchar(5) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `key` varchar(32) NOT NULL,
  `distinction` tinyint(1) NOT NULL,
  `status` varchar(32) NOT NULL,
  `verify_uuid` varchar(32) NOT NULL,
  `download_uuid` varchar(32) NOT NULL,
  `name` varchar(255) NOT NULL,
  `created_date` datetime NOT NULL,
  `modified_date` datetime NOT NULL,
  `error_reason` varchar(512) NOT NULL,
  `mode` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificates_generatedcertifica_course_id_1389f6b2d72f5e78_uniq` (`course_id`,`user_id`),
  KEY `certificates_generatedcertificate_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_6c4fb3478e23bfe2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `circuit_servercircuit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `circuit_servercircuit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `schematic` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_courseusergroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_courseusergroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `group_type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`,`course_id`),
  KEY `course_groups_courseusergroup_ff48d8e5` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_courseusergroup_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_courseusergroup_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `courseusergroup_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseusergroup_id` (`courseusergroup_id`,`user_id`),
  KEY `course_groups_courseusergroup_users_caee1c64` (`courseusergroup_id`),
  KEY `course_groups_courseusergroup_users_fbfc09f1` (`user_id`),
  CONSTRAINT `courseusergroup_id_refs_id_d26180aa` FOREIGN KEY (`courseusergroup_id`) REFERENCES `course_groups_courseusergroup` (`id`),
  CONSTRAINT `user_id_refs_id_bf33b47a` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_modes_coursemode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_modes_coursemode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `mode_slug` varchar(100) NOT NULL,
  `mode_display_name` varchar(255) NOT NULL,
  `min_price` int(11) NOT NULL,
  `suggested_prices` varchar(255) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `expiration_date` date DEFAULT NULL,
  `expiration_datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_modes_coursemode_course_id_69505c92fc09856_uniq` (`course_id`,`currency`,`mode_slug`),
  KEY `course_modes_coursemode_ff48d8e5` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_offlinecomputedgrade`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_offlinecomputedgrade` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime NOT NULL,
  `gradeset` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_offlinecomputedgrade_user_id_46133bbd0926078f_uniq` (`user_id`,`course_id`),
  KEY `courseware_offlinecomputedgrade_fbfc09f1` (`user_id`),
  KEY `courseware_offlinecomputedgrade_ff48d8e5` (`course_id`),
  KEY `courseware_offlinecomputedgrade_3216ff68` (`created`),
  KEY `courseware_offlinecomputedgrade_8aac229` (`updated`),
  CONSTRAINT `user_id_refs_id_7b3221f638cf339d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_offlinecomputedgradelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_offlinecomputedgradelog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created` datetime DEFAULT NULL,
  `seconds` int(11) NOT NULL,
  `nstudents` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `courseware_offlinecomputedgradelog_ff48d8e5` (`course_id`),
  KEY `courseware_offlinecomputedgradelog_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_studentmodule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_studentmodule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `module_type` varchar(32) NOT NULL,
  `module_id` varchar(255) NOT NULL,
  `student_id` int(11) NOT NULL,
  `state` longtext,
  `grade` double DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `max_grade` double DEFAULT NULL,
  `done` varchar(8) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_studentmodule_student_id_635d77aea1256de5_uniq` (`student_id`,`module_id`,`course_id`),
  KEY `courseware_studentmodule_42ff452e` (`student_id`),
  KEY `courseware_studentmodule_3216ff68` (`created`),
  KEY `courseware_studentmodule_6dff86b5` (`grade`),
  KEY `courseware_studentmodule_5436e97a` (`modified`),
  KEY `courseware_studentmodule_2d8768ff` (`module_type`),
  KEY `courseware_studentmodule_f53ed95e` (`module_id`),
  KEY `courseware_studentmodule_1923c03f` (`done`),
  KEY `courseware_studentmodule_ff48d8e5` (`course_id`),
  CONSTRAINT `student_id_refs_id_51af713179ba2570` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_studentmodulehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_studentmodulehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_module_id` int(11) NOT NULL,
  `version` varchar(255) DEFAULT NULL,
  `created` datetime NOT NULL,
  `state` longtext,
  `grade` double DEFAULT NULL,
  `max_grade` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `courseware_studentmodulehistory_5656f5fe` (`student_module_id`),
  KEY `courseware_studentmodulehistory_659105e4` (`version`),
  KEY `courseware_studentmodulehistory_3216ff68` (`created`),
  CONSTRAINT `student_module_id_refs_id_51904344e48636f4` FOREIGN KEY (`student_module_id`) REFERENCES `courseware_studentmodule` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmodulestudentinfofield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmodulestudentinfofield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `value` longtext NOT NULL,
  `student_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmodulestudentinfof_student_id_33f2f772c49db067_uniq` (`student_id`,`field_name`),
  KEY `courseware_xmodulestudentinfofield_7e1499` (`field_name`),
  KEY `courseware_xmodulestudentinfofield_42ff452e` (`student_id`),
  KEY `courseware_xmodulestudentinfofield_3216ff68` (`created`),
  KEY `courseware_xmodulestudentinfofield_5436e97a` (`modified`),
  CONSTRAINT `student_id_refs_id_66e06928bfcfbe68` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmodulestudentprefsfield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmodulestudentprefsfield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `module_type` varchar(64) NOT NULL,
  `value` longtext NOT NULL,
  `student_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmodulestudentprefs_student_id_2a5d275498b7a407_uniq` (`student_id`,`module_type`,`field_name`),
  KEY `courseware_xmodulestudentprefsfield_7e1499` (`field_name`),
  KEY `courseware_xmodulestudentprefsfield_2d8768ff` (`module_type`),
  KEY `courseware_xmodulestudentprefsfield_42ff452e` (`student_id`),
  KEY `courseware_xmodulestudentprefsfield_3216ff68` (`created`),
  KEY `courseware_xmodulestudentprefsfield_5436e97a` (`modified`),
  CONSTRAINT `student_id_refs_id_32bbaa45d7b9940b` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmoduleuserstatesummaryfield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmoduleuserstatesummaryfield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `usage_id` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmodulecontentfi_definition_id_50fa4fd570cf2f4a_uniq` (`usage_id`,`field_name`),
  KEY `courseware_xmodulecontentfield_7e1499` (`field_name`),
  KEY `courseware_xmodulecontentfield_1d304ded` (`usage_id`),
  KEY `courseware_xmodulecontentfield_3216ff68` (`created`),
  KEY `courseware_xmodulecontentfield_5436e97a` (`modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_fbfc09f1` (`user_id`),
  KEY `django_admin_log_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_comment_client_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comment_client_permission` (
  `name` varchar(30) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_comment_client_permission_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comment_client_permission_roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `permission_id` varchar(30) NOT NULL,
  `role_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_comment_client_permi_permission_id_7a766da089425952_uniq` (`permission_id`,`role_id`),
  KEY `django_comment_client_permission_roles_1e014c8f` (`permission_id`),
  KEY `django_comment_client_permission_roles_bf07f040` (`role_id`),
  CONSTRAINT `role_id_refs_id_6ccffe4ec1b5c854` FOREIGN KEY (`role_id`) REFERENCES `django_comment_client_role` (`id`),
  CONSTRAINT `permission_id_refs_name_63b5ab82b6302d27` FOREIGN KEY (`permission_id`) REFERENCES `django_comment_client_permission` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_comment_client_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comment_client_role` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_comment_client_role_ff48d8e5` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_comment_client_role_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comment_client_role_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_comment_client_role_users_role_id_78e483f531943614_uniq` (`role_id`,`user_id`),
  KEY `django_comment_client_role_users_bf07f040` (`role_id`),
  KEY `django_comment_client_role_users_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_60d02531441b79e7` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `role_id_refs_id_282d08d1ab82c838` FOREIGN KEY (`role_id`) REFERENCES `django_comment_client_role` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_openid_auth_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_openid_auth_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_url` longtext NOT NULL,
  `handle` varchar(255) NOT NULL,
  `secret` longtext NOT NULL,
  `issued` int(11) NOT NULL,
  `lifetime` int(11) NOT NULL,
  `assoc_type` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_openid_auth_nonce`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_openid_auth_nonce` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_url` varchar(2047) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `salt` varchar(40) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_openid_auth_useropenid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_openid_auth_useropenid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `claimed_id` longtext NOT NULL,
  `display_id` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_openid_auth_useropenid_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_be7162f0` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_c25c2c28` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_crontabschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `minute` varchar(64) NOT NULL,
  `hour` varchar(64) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  `day_of_month` varchar(64) NOT NULL,
  `month_of_year` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_intervalschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `every` int(11) NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `interval_id` int(11) DEFAULT NULL,
  `crontab_id` int(11) DEFAULT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `djcelery_periodictask_17d2d99d` (`interval_id`),
  KEY `djcelery_periodictask_7aa5fda` (`crontab_id`),
  CONSTRAINT `interval_id_refs_id_f2054349` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`),
  CONSTRAINT `crontab_id_refs_id_ebff5e74` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_taskstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_taskstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` varchar(64) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `tstamp` datetime NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `retries` int(11) NOT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `djcelery_taskstate_355bfc27` (`state`),
  KEY `djcelery_taskstate_52094d6e` (`name`),
  KEY `djcelery_taskstate_f0ba6500` (`tstamp`),
  KEY `djcelery_taskstate_20fc5b84` (`worker_id`),
  KEY `djcelery_taskstate_c91f1bf` (`hidden`),
  CONSTRAINT `worker_id_refs_id_4e3453a` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_workerstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  KEY `djcelery_workerstate_eb8ac7e4` (`last_heartbeat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `external_auth_externalauthmap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `external_auth_externalauthmap` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `external_id` varchar(255) NOT NULL,
  `external_domain` varchar(255) NOT NULL,
  `external_credentials` longtext NOT NULL,
  `external_email` varchar(255) NOT NULL,
  `external_name` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `internal_password` varchar(31) NOT NULL,
  `dtcreated` datetime NOT NULL,
  `dtsignup` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_auth_externalauthmap_external_id_7f035ef8bc4d313e_uniq` (`external_id`,`external_domain`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `external_auth_externalauthmap_d5e787` (`external_id`),
  KEY `external_auth_externalauthmap_a570024c` (`external_domain`),
  KEY `external_auth_externalauthmap_a142061d` (`external_email`),
  KEY `external_auth_externalauthmap_c1a016f` (`external_name`),
  CONSTRAINT `user_id_refs_id_39c4e675f8635f67` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `foldit_puzzlecomplete`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foldit_puzzlecomplete` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `unique_user_id` varchar(50) NOT NULL,
  `puzzle_id` int(11) NOT NULL,
  `puzzle_set` int(11) NOT NULL,
  `puzzle_subset` int(11) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `foldit_puzzlecomplete_user_id_4c63656af6674331_uniq` (`user_id`,`puzzle_id`,`puzzle_set`,`puzzle_subset`),
  KEY `foldit_puzzlecomplete_fbfc09f1` (`user_id`),
  KEY `foldit_puzzlecomplete_8027477e` (`unique_user_id`),
  KEY `foldit_puzzlecomplete_4798a2b8` (`puzzle_set`),
  KEY `foldit_puzzlecomplete_59f06bcd` (`puzzle_subset`),
  CONSTRAINT `user_id_refs_id_23bb09ab37e9437b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `foldit_score`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foldit_score` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `unique_user_id` varchar(50) NOT NULL,
  `puzzle_id` int(11) NOT NULL,
  `best_score` double NOT NULL,
  `current_score` double NOT NULL,
  `score_version` int(11) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `foldit_score_fbfc09f1` (`user_id`),
  KEY `foldit_score_8027477e` (`unique_user_id`),
  KEY `foldit_score_3624c060` (`best_score`),
  KEY `foldit_score_b4627792` (`current_score`),
  CONSTRAINT `user_id_refs_id_44efb56f4c07957f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `instructor_task_instructortask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instructor_task_instructortask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_type` varchar(50) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `task_key` varchar(255) NOT NULL,
  `task_input` varchar(255) NOT NULL,
  `task_id` varchar(255) NOT NULL,
  `task_state` varchar(50) DEFAULT NULL,
  `task_output` varchar(1024) DEFAULT NULL,
  `requester_id` int(11) NOT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime NOT NULL,
  `subtasks` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `instructor_task_instructortask_8ae638b4` (`task_type`),
  KEY `instructor_task_instructortask_ff48d8e5` (`course_id`),
  KEY `instructor_task_instructortask_cfc55170` (`task_key`),
  KEY `instructor_task_instructortask_c00fe455` (`task_id`),
  KEY `instructor_task_instructortask_731e67a4` (`task_state`),
  KEY `instructor_task_instructortask_b8ca8b9f` (`requester_id`),
  CONSTRAINT `requester_id_refs_id_4d6b69c6a97278e6` FOREIGN KEY (`requester_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `licenses_coursesoftware`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `licenses_coursesoftware` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `url` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `licenses_userlicense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `licenses_userlicense` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `software_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `serial` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `licenses_userlicense_4c6ed3c1` (`software_id`),
  KEY `licenses_userlicense_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_26345de02f3a1cb3` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `software_id_refs_id_78738fcdf9e27be8` FOREIGN KEY (`software_id`) REFERENCES `licenses_coursesoftware` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `linkedin_linkedin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `linkedin_linkedin` (
  `user_id` int(11) NOT NULL,
  `has_linkedin_account` tinyint(1) DEFAULT NULL,
  `emailed_courses` longtext NOT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_id_refs_id_7b29e97d72e31bb2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notes_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notes_note` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `uri` varchar(255) NOT NULL,
  `text` longtext NOT NULL,
  `quote` longtext NOT NULL,
  `range_start` varchar(2048) NOT NULL,
  `range_start_offset` int(11) NOT NULL,
  `range_end` varchar(2048) NOT NULL,
  `range_end_offset` int(11) NOT NULL,
  `tags` longtext NOT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notes_note_fbfc09f1` (`user_id`),
  KEY `notes_note_ff48d8e5` (`course_id`),
  KEY `notes_note_a9794fa` (`uri`),
  KEY `notes_note_3216ff68` (`created`),
  KEY `notes_note_8aac229` (`updated`),
  CONSTRAINT `user_id_refs_id_380a4734360715cc` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notifications_articlesubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_articlesubscription` (
  `subscription_ptr_id` int(11) NOT NULL,
  `articleplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  UNIQUE KEY `subscription_ptr_id` (`subscription_ptr_id`),
  CONSTRAINT `articleplugin_ptr_id_refs_id_1bd08ac071ed584a` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`),
  CONSTRAINT `subscription_ptr_id_refs_id_18f7bae575c0b518` FOREIGN KEY (`subscription_ptr_id`) REFERENCES `notify_subscription` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_notification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subscription_id` int(11) DEFAULT NULL,
  `message` longtext NOT NULL,
  `url` varchar(200) DEFAULT NULL,
  `is_viewed` tinyint(1) NOT NULL,
  `is_emailed` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notify_notification_104f5ac1` (`subscription_id`),
  CONSTRAINT `subscription_id_refs_id_7a99ebc5baf93d4f` FOREIGN KEY (`subscription_id`) REFERENCES `notify_subscription` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_notificationtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_notificationtype` (
  `key` varchar(128) NOT NULL,
  `label` varchar(128) DEFAULT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`key`),
  KEY `notify_notificationtype_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_4919de6f2478378` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `interval` smallint(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notify_settings_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_2e6a6a1d9a2911e6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `settings_id` int(11) NOT NULL,
  `notification_type_id` varchar(128) NOT NULL,
  `object_id` varchar(64) DEFAULT NULL,
  `send_emails` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notify_subscription_83326d99` (`settings_id`),
  KEY `notify_subscription_9955f091` (`notification_type_id`),
  CONSTRAINT `notification_type_id_refs_key_25426c9bbaa41a19` FOREIGN KEY (`notification_type_id`) REFERENCES `notify_notificationtype` (`key`),
  CONSTRAINT `settings_id_refs_id_2b8d6d653b7225d5` FOREIGN KEY (`settings_id`) REFERENCES `notify_settings` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `psychometrics_psychometricdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `psychometrics_psychometricdata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `studentmodule_id` int(11) NOT NULL,
  `done` tinyint(1) NOT NULL,
  `attempts` int(11) NOT NULL,
  `checktimes` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `studentmodule_id` (`studentmodule_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_certificateitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_certificateitem` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  `course_enrollment_id` int(11) NOT NULL,
  `mode` varchar(50) NOT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `shoppingcart_certificateitem_ff48d8e5` (`course_id`),
  KEY `shoppingcart_certificateitem_9e513f0b` (`course_enrollment_id`),
  KEY `shoppingcart_certificateitem_4160619e` (`mode`),
  CONSTRAINT `course_enrollment_id_refs_id_259181e58048c435` FOREIGN KEY (`course_enrollment_id`) REFERENCES `student_courseenrollment` (`id`),
  CONSTRAINT `orderitem_ptr_id_refs_id_4d598262d3ebc4d0` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_order` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `status` varchar(32) NOT NULL,
  `purchase_time` datetime DEFAULT NULL,
  `bill_to_first` varchar(64) NOT NULL,
  `bill_to_last` varchar(64) NOT NULL,
  `bill_to_street1` varchar(128) NOT NULL,
  `bill_to_street2` varchar(128) NOT NULL,
  `bill_to_city` varchar(64) NOT NULL,
  `bill_to_state` varchar(8) NOT NULL,
  `bill_to_postalcode` varchar(16) NOT NULL,
  `bill_to_country` varchar(64) NOT NULL,
  `bill_to_ccnum` varchar(8) NOT NULL,
  `bill_to_cardtype` varchar(32) NOT NULL,
  `processor_reply_dump` longtext NOT NULL,
  `refunded_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_order_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_a4b0342e1195673` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_orderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_orderitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `status` varchar(32) NOT NULL,
  `qty` int(11) NOT NULL,
  `unit_cost` decimal(30,2) NOT NULL,
  `line_desc` varchar(1024) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `fulfilled_time` datetime DEFAULT NULL,
  `report_comments` longtext NOT NULL,
  `refund_requested_time` datetime DEFAULT NULL,
  `service_fee` decimal(30,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_orderitem_8337030b` (`order_id`),
  KEY `shoppingcart_orderitem_fbfc09f1` (`user_id`),
  KEY `shoppingcart_orderitem_c9ad71dd` (`status`),
  KEY `shoppingcart_orderitem_8457f26a` (`fulfilled_time`),
  KEY `shoppingcart_orderitem_416112c1` (`refund_requested_time`),
  CONSTRAINT `order_id_refs_id_4fad6e867c77b3f0` FOREIGN KEY (`order_id`) REFERENCES `shoppingcart_order` (`id`),
  CONSTRAINT `user_id_refs_id_608b9042d92ae410` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_paidcourseregistration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_paidcourseregistration` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  `mode` varchar(50) NOT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `shoppingcart_paidcourseregistration_ff48d8e5` (`course_id`),
  KEY `shoppingcart_paidcourseregistration_4160619e` (`mode`),
  CONSTRAINT `orderitem_ptr_id_refs_id_c5c6141d8709d99` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_paidcourseregistrationannotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_paidcourseregistrationannotation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(128) NOT NULL,
  `annotation` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `south_migrationhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `south_migrationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) NOT NULL,
  `migration` varchar(255) NOT NULL,
  `applied` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=114 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_anonymoususerid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_anonymoususerid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `anonymous_user_id` varchar(32) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `anonymous_user_id` (`anonymous_user_id`),
  KEY `student_anonymoususerid_fbfc09f1` (`user_id`),
  KEY `student_anonymoususerid_ff48d8e5` (`course_id`),
  CONSTRAINT `user_id_refs_id_23effb36c38f7a2a` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseenrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseenrollment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `created` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `mode` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_courseenrollment_user_id_2d2a572f07dd8e37_uniq` (`user_id`,`course_id`),
  KEY `student_courseenrollment_fbfc09f1` (`user_id`),
  KEY `student_courseenrollment_ff48d8e5` (`course_id`),
  KEY `student_courseenrollment_3216ff68` (`created`),
  CONSTRAINT `user_id_refs_id_45948fcded37bc9d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseenrollmentallowed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseenrollmentallowed` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `created` datetime DEFAULT NULL,
  `auto_enroll` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_courseenrollmentallowed_email_6f3eafd4a6c58591_uniq` (`email`,`course_id`),
  KEY `student_courseenrollmentallowed_3904588a` (`email`),
  KEY `student_courseenrollmentallowed_ff48d8e5` (`course_id`),
  KEY `student_courseenrollmentallowed_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_pendingemailchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_pendingemailchange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `new_email` varchar(255) NOT NULL,
  `activation_key` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `activation_key` (`activation_key`),
  KEY `student_pendingemailchange_856c86d7` (`new_email`),
  CONSTRAINT `user_id_refs_id_24fa3bcda525fa67` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_pendingnamechange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_pendingnamechange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `new_name` varchar(255) NOT NULL,
  `rationale` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_24e959cdd9359b27` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_userstanding`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_userstanding` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `account_status` varchar(31) NOT NULL,
  `changed_by_id` int(11) NOT NULL,
  `standing_last_changed_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `student_userstanding_16905482` (`changed_by_id`),
  CONSTRAINT `changed_by_id_refs_id_5ec33b2b0450a33b` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `user_id_refs_id_5ec33b2b0450a33b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_usertestgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_usertestgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `student_usertestgroup_52094d6e` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_usertestgroup_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_usertestgroup_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usertestgroup_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_usertestgroup_us_usertestgroup_id_63c588e0372991b0_uniq` (`usertestgroup_id`,`user_id`),
  KEY `student_usertestgroup_users_44f27cdf` (`usertestgroup_id`),
  KEY `student_usertestgroup_users_fbfc09f1` (`user_id`),
  CONSTRAINT `usertestgroup_id_refs_id_78e186d36d724f9e` FOREIGN KEY (`usertestgroup_id`) REFERENCES `student_usertestgroup` (`id`),
  CONSTRAINT `user_id_refs_id_412b14bf8947584c` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `track_trackinglog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `track_trackinglog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtcreated` datetime NOT NULL,
  `username` varchar(32) NOT NULL,
  `ip` varchar(32) NOT NULL,
  `event_source` varchar(32) NOT NULL,
  `event_type` varchar(512) NOT NULL,
  `event` longtext NOT NULL,
  `agent` varchar(256) NOT NULL,
  `page` varchar(512) DEFAULT NULL,
  `time` datetime NOT NULL,
  `host` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `user_api_userpreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_api_userpreference` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `key` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_api_userpreference_user_id_4e4942d73f760072_uniq` (`user_id`,`key`),
  KEY `user_api_userpreference_fbfc09f1` (`user_id`),
  KEY `user_api_userpreference_45544485` (`key`),
  CONSTRAINT `user_id_refs_id_2839c1f4f3473b9e` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_softwaresecurephotoverification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_softwaresecurephotoverification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status` varchar(100) NOT NULL,
  `status_changed` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `face_image_url` varchar(255) NOT NULL,
  `photo_id_image_url` varchar(255) NOT NULL,
  `receipt_id` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `reviewing_user_id` int(11) DEFAULT NULL,
  `reviewing_service` varchar(255) NOT NULL,
  `error_msg` longtext NOT NULL,
  `error_code` varchar(50) NOT NULL,
  `photo_id_key` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `verify_student_softwaresecurephotoverification_fbfc09f1` (`user_id`),
  KEY `verify_student_softwaresecurephotoverification_8713c555` (`receipt_id`),
  KEY `verify_student_softwaresecurephotoverification_3b1c9c31` (`created_at`),
  KEY `verify_student_softwaresecurephotoverification_f84f7de6` (`updated_at`),
  KEY `verify_student_softwaresecurephotoverification_4452d192` (`submitted_at`),
  KEY `verify_student_softwaresecurephotoverification_b2c165b4` (`reviewing_user_id`),
  CONSTRAINT `reviewing_user_id_refs_id_5b90d52ad6ea4207` FOREIGN KEY (`reviewing_user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `user_id_refs_id_5b90d52ad6ea4207` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `waffle_flag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `everyone` tinyint(1) DEFAULT NULL,
  `percent` decimal(3,1) DEFAULT NULL,
  `superusers` tinyint(1) NOT NULL,
  `staff` tinyint(1) NOT NULL,
  `authenticated` tinyint(1) NOT NULL,
  `rollout` tinyint(1) NOT NULL,
  `note` longtext NOT NULL,
  `testing` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `languages` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_flag_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `waffle_flag_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flag_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `waffle_flag_groups_flag_id_582896076571ab8b_uniq` (`flag_id`,`group_id`),
  KEY `waffle_flag_groups_9bca17e2` (`flag_id`),
  KEY `waffle_flag_groups_bda51c3c` (`group_id`),
  CONSTRAINT `group_id_refs_id_66545bd34ea49f34` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `flag_id_refs_id_6f1b152a8e6a807d` FOREIGN KEY (`flag_id`) REFERENCES `waffle_flag` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `waffle_flag_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flag_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `waffle_flag_users_flag_id_3bb77386107938a3_uniq` (`flag_id`,`user_id`),
  KEY `waffle_flag_users_9bca17e2` (`flag_id`),
  KEY `waffle_flag_users_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_1fe1cfb8bae2dfc2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `flag_id_refs_id_5034023d8fef0c12` FOREIGN KEY (`flag_id`) REFERENCES `waffle_flag` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `waffle_sample`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_sample` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `percent` decimal(4,1) NOT NULL,
  `note` longtext NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_sample_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `waffle_switch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_switch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `note` longtext NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_switch_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_article` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `current_revision_id` int(11) DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `group_id` int(11) DEFAULT NULL,
  `group_read` tinyint(1) NOT NULL,
  `group_write` tinyint(1) NOT NULL,
  `other_read` tinyint(1) NOT NULL,
  `other_write` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  KEY `wiki_article_5d52dd10` (`owner_id`),
  KEY `wiki_article_bda51c3c` (`group_id`),
  CONSTRAINT `group_id_refs_id_10e2d3dd108bfee4` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `current_revision_id_refs_id_1d8d320ebafac304` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `owner_id_refs_id_18073b359e14b583` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articleforobject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articleforobject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `article_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `is_mptt` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_articleforobject_content_type_id_27c4cce189b3bcab_uniq` (`content_type_id`,`object_id`),
  KEY `wiki_articleforobject_30525a19` (`article_id`),
  KEY `wiki_articleforobject_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_6b30567037828764` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `article_id_refs_id_1698e37305099436` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articleplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articleplugin` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `article_id` int(11) NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_articleplugin_30525a19` (`article_id`),
  CONSTRAINT `article_id_refs_id_64fa106f92c648ca` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articlerevision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articlerevision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `revision_number` int(11) NOT NULL,
  `user_message` longtext NOT NULL,
  `automatic_log` longtext NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `modified` datetime NOT NULL,
  `created` datetime NOT NULL,
  `previous_revision_id` int(11) DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `article_id` int(11) NOT NULL,
  `content` longtext NOT NULL,
  `title` varchar(512) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_articlerevision_article_id_4b4e7910c8e7b2d0_uniq` (`article_id`,`revision_number`),
  KEY `wiki_articlerevision_fbfc09f1` (`user_id`),
  KEY `wiki_articlerevision_49bc38cc` (`previous_revision_id`),
  KEY `wiki_articlerevision_30525a19` (`article_id`),
  CONSTRAINT `article_id_refs_id_5a3b45ce5c88570a` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`),
  CONSTRAINT `previous_revision_id_refs_id_7c6fe338a951e36b` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `user_id_refs_id_672c6e4dfbb26714` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articlesubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articlesubscription` (
  `subscription_ptr_id` int(11) NOT NULL,
  `articleplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  UNIQUE KEY `subscription_ptr_id` (`subscription_ptr_id`),
  CONSTRAINT `articleplugin_ptr_id_refs_id_7b2f9df4cbce00e3` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`),
  CONSTRAINT `subscription_ptr_id_refs_id_4ec3f6dbae89f475` FOREIGN KEY (`subscription_ptr_id`) REFERENCES `notify_subscription` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_attachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_attachment` (
  `reusableplugin_ptr_id` int(11) NOT NULL,
  `current_revision_id` int(11) DEFAULT NULL,
  `original_filename` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`reusableplugin_ptr_id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  CONSTRAINT `current_revision_id_refs_id_66561e6e2198feb4` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_attachmentrevision` (`id`),
  CONSTRAINT `reusableplugin_ptr_id_refs_articleplugin_ptr_id_79d179a16644e87a` FOREIGN KEY (`reusableplugin_ptr_id`) REFERENCES `wiki_reusableplugin` (`articleplugin_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_attachmentrevision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_attachmentrevision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `revision_number` int(11) NOT NULL,
  `user_message` longtext NOT NULL,
  `automatic_log` longtext NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `modified` datetime NOT NULL,
  `created` datetime NOT NULL,
  `previous_revision_id` int(11) DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `attachment_id` int(11) NOT NULL,
  `file` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_attachmentrevision_fbfc09f1` (`user_id`),
  KEY `wiki_attachmentrevision_49bc38cc` (`previous_revision_id`),
  KEY `wiki_attachmentrevision_edee6011` (`attachment_id`),
  CONSTRAINT `attachment_id_refs_reusableplugin_ptr_id_33d8cf1f640583da` FOREIGN KEY (`attachment_id`) REFERENCES `wiki_attachment` (`reusableplugin_ptr_id`),
  CONSTRAINT `previous_revision_id_refs_id_5521ecec0041bbf5` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_attachmentrevision` (`id`),
  CONSTRAINT `user_id_refs_id_2822eb682eaca84c` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_image` (
  `revisionplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`revisionplugin_ptr_id`),
  CONSTRAINT `revisionplugin_ptr_id_refs_articleplugin_ptr_id_1a20f885fc42a0b1` FOREIGN KEY (`revisionplugin_ptr_id`) REFERENCES `wiki_revisionplugin` (`articleplugin_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_imagerevision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_imagerevision` (
  `revisionpluginrevision_ptr_id` int(11) NOT NULL,
  `image` varchar(2000) DEFAULT NULL,
  `width` smallint(6) DEFAULT NULL,
  `height` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`revisionpluginrevision_ptr_id`),
  CONSTRAINT `revisionpluginrevision_ptr_id_refs_id_5da3ee545b9fc791` FOREIGN KEY (`revisionpluginrevision_ptr_id`) REFERENCES `wiki_revisionpluginrevision` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_reusableplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_reusableplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  CONSTRAINT `articleplugin_ptr_id_refs_id_2a5c48de4ca661fd` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_reusableplugin_articles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_reusableplugin_articles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reusableplugin_id` int(11) NOT NULL,
  `article_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_reusableplugin_art_reusableplugin_id_6e34ac94afa8f9f2_uniq` (`reusableplugin_id`,`article_id`),
  KEY `wiki_reusableplugin_articles_28b0b358` (`reusableplugin_id`),
  KEY `wiki_reusableplugin_articles_30525a19` (`article_id`),
  CONSTRAINT `article_id_refs_id_854477c2f51faad` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`),
  CONSTRAINT `reusableplugin_id_refs_articleplugin_ptr_id_496cabe744b45e30` FOREIGN KEY (`reusableplugin_id`) REFERENCES `wiki_reusableplugin` (`articleplugin_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_revisionplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_revisionplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  `current_revision_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  CONSTRAINT `current_revision_id_refs_id_2732d4b244938e26` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revisionpluginrevision` (`id`),
  CONSTRAINT `articleplugin_ptr_id_refs_id_2b8f815fcac31401` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_revisionpluginrevision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_revisionpluginrevision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `revision_number` int(11) NOT NULL,
  `user_message` longtext NOT NULL,
  `automatic_log` longtext NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `modified` datetime NOT NULL,
  `created` datetime NOT NULL,
  `previous_revision_id` int(11) DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `plugin_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_revisionpluginrevision_fbfc09f1` (`user_id`),
  KEY `wiki_revisionpluginrevision_49bc38cc` (`previous_revision_id`),
  KEY `wiki_revisionpluginrevision_2857ccbf` (`plugin_id`),
  CONSTRAINT `plugin_id_refs_articleplugin_ptr_id_3e044eb541bbc69c` FOREIGN KEY (`plugin_id`) REFERENCES `wiki_revisionplugin` (`articleplugin_ptr_id`),
  CONSTRAINT `previous_revision_id_refs_id_3348918678fffe43` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_revisionpluginrevision` (`id`),
  CONSTRAINT `user_id_refs_id_21540d2c32d8f395` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_simpleplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_simpleplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  `article_revision_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  KEY `wiki_simpleplugin_b3dc49fe` (`article_revision_id`),
  CONSTRAINT `article_revision_id_refs_id_2252033b6df37b12` FOREIGN KEY (`article_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `articleplugin_ptr_id_refs_id_6704e8c7a25cbfd2` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_urlpath`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_urlpath` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `slug` varchar(50) DEFAULT NULL,
  `site_id` int(11) NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `lft` int(10) unsigned NOT NULL,
  `rght` int(10) unsigned NOT NULL,
  `tree_id` int(10) unsigned NOT NULL,
  `level` int(10) unsigned NOT NULL,
  `article_id` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_urlpath_site_id_124f6aa7b2cc9b82_uniq` (`site_id`,`parent_id`,`slug`),
  KEY `wiki_urlpath_a951d5d6` (`slug`),
  KEY `wiki_urlpath_6223029` (`site_id`),
  KEY `wiki_urlpath_63f17a16` (`parent_id`),
  KEY `wiki_urlpath_42b06ff6` (`lft`),
  KEY `wiki_urlpath_91543e5a` (`rght`),
  KEY `wiki_urlpath_efd07f28` (`tree_id`),
  KEY `wiki_urlpath_2a8f42e8` (`level`),
  KEY `wiki_urlpath_30525a19` (`article_id`),
  CONSTRAINT `article_id_refs_id_23bd80e7971759c9` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`),
  CONSTRAINT `parent_id_refs_id_62afe7c752d1e703` FOREIGN KEY (`parent_id`) REFERENCES `wiki_urlpath` (`id`),
  CONSTRAINT `site_id_refs_id_462d2bc7f4bbaaa2` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

