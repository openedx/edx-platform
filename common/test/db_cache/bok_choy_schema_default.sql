
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
DROP TABLE IF EXISTS `api_admin_apiaccessconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_admin_apiaccessconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `api_admin_apiacce_changed_by_id_771a504ee92a076c_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `api_admin_apiacce_changed_by_id_771a504ee92a076c_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `api_admin_apiaccessrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_admin_apiaccessrequest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `status` varchar(255) NOT NULL,
  `website` varchar(200) NOT NULL,
  `reason` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  `company_address` varchar(255) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `contacted` tinyint(1) NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `api_admin_apiaccessrequest_user_id_6753e50e296cabc7_uniq` (`user_id`),
  KEY `api_admin_apiaccessrequest_9acb4454` (`status`),
  KEY `api_admin_apiaccessrequest_9365d6e7` (`site_id`),
  CONSTRAINT `api_admin_apiaccessre_site_id_7963330a765f8041_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`),
  CONSTRAINT `api_admin_apiaccessrequ_user_id_6753e50e296cabc7_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `api_admin_historicalapiaccessrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_admin_historicalapiaccessrequest` (
  `id` int(11) NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `status` varchar(255) NOT NULL,
  `website` varchar(200) NOT NULL,
  `reason` longtext NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `company_address` varchar(255) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `contacted` tinyint(1) NOT NULL,
  `site_id` int(11),
  PRIMARY KEY (`history_id`),
  KEY `api_admin_histo_history_user_id_73c59297a81bcd02_fk_auth_user_id` (`history_user_id`),
  KEY `api_admin_historicalapiaccessrequest_b80bb774` (`id`),
  KEY `api_admin_historicalapiaccessrequest_9acb4454` (`status`),
  KEY `api_admin_historicalapiaccessrequest_9365d6e7` (`site_id`),
  CONSTRAINT `api_admin_histo_history_user_id_73c59297a81bcd02_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_aiclassifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_aiclassifier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `classifier_data` varchar(100) NOT NULL,
  `classifier_set_id` int(11) NOT NULL,
  `criterion_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assessment_aiclassifier_962f069f` (`classifier_set_id`),
  KEY `assessment_aiclassifier_385b00a3` (`criterion_id`),
  CONSTRAINT `D3bd45d5e3c9cfdc4f3b442119adebe8` FOREIGN KEY (`classifier_set_id`) REFERENCES `assessment_aiclassifierset` (`id`),
  CONSTRAINT `assessm_criterion_id_275db29f2a0e1711_fk_assessment_criterion_id` FOREIGN KEY (`criterion_id`) REFERENCES `assessment_criterion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_aiclassifierset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_aiclassifierset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `algorithm_id` varchar(128) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `rubric_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assessment_aiclassifierset_fde81f11` (`created_at`),
  KEY `assessment_aiclassifierset_65143c91` (`algorithm_id`),
  KEY `assessment_aiclassifierset_ea134da7` (`course_id`),
  KEY `assessment_aiclassifierset_82bfda79` (`item_id`),
  KEY `assessment_aiclassifierset_8980b7ae` (`rubric_id`),
  CONSTRAINT `assessment_ai_rubric_id_45488be94ea0aea5_fk_assessment_rubric_id` FOREIGN KEY (`rubric_id`) REFERENCES `assessment_rubric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_aigradingworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_aigradingworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `scheduled_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `algorithm_id` varchar(128) NOT NULL,
  `submission_uuid` varchar(128) NOT NULL,
  `essay_text` longtext NOT NULL,
  `student_id` varchar(40) NOT NULL,
  `assessment_id` int(11) DEFAULT NULL,
  `classifier_set_id` int(11) DEFAULT NULL,
  `rubric_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `assessment_aigradingworkflow_ea134da7` (`course_id`),
  KEY `assessment_aigradingworkflow_82bfda79` (`item_id`),
  KEY `assessment_aigradingworkflow_96e4551c` (`scheduled_at`),
  KEY `assessment_aigradingworkflow_4430a679` (`completed_at`),
  KEY `assessment_aigradingworkflow_65143c91` (`algorithm_id`),
  KEY `assessment_aigradingworkflow_ab5b2b73` (`submission_uuid`),
  KEY `assessment_aigradingworkflow_30a811f6` (`student_id`),
  KEY `assessment_aigradingworkflow_a4079fcf` (`assessment_id`),
  KEY `assessment_aigradingworkflow_962f069f` (`classifier_set_id`),
  KEY `assessment_aigradingworkflow_8980b7ae` (`rubric_id`),
  CONSTRAINT `D4d9bca115376aeb07fd970155499db3` FOREIGN KEY (`classifier_set_id`) REFERENCES `assessment_aiclassifierset` (`id`),
  CONSTRAINT `asses_assessment_id_68b86880a7f62f1c_fk_assessment_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `assessment_assessment` (`id`),
  CONSTRAINT `assessment_ai_rubric_id_3fc938e9e3ae7b2d_fk_assessment_rubric_id` FOREIGN KEY (`rubric_id`) REFERENCES `assessment_rubric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_aitrainingworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_aitrainingworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `scheduled_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `algorithm_id` varchar(128) NOT NULL,
  `classifier_set_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fb3b73b224dc39eb386f5d3ec67998b7` (`classifier_set_id`),
  KEY `assessment_aitrainingworkflow_ea134da7` (`course_id`),
  KEY `assessment_aitrainingworkflow_82bfda79` (`item_id`),
  KEY `assessment_aitrainingworkflow_96e4551c` (`scheduled_at`),
  KEY `assessment_aitrainingworkflow_4430a679` (`completed_at`),
  KEY `assessment_aitrainingworkflow_65143c91` (`algorithm_id`),
  CONSTRAINT `fb3b73b224dc39eb386f5d3ec67998b7` FOREIGN KEY (`classifier_set_id`) REFERENCES `assessment_aiclassifierset` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_aitrainingworkflow_training_examples`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_aitrainingworkflow_training_examples` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `aitrainingworkflow_id` int(11) NOT NULL,
  `trainingexample_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `aitrainingworkflow_id` (`aitrainingworkflow_id`,`trainingexample_id`),
  KEY `ff4ddecc43bd06c0d85785a61e955133` (`trainingexample_id`),
  CONSTRAINT `da55be90caee21d95136e40c53e5c754` FOREIGN KEY (`aitrainingworkflow_id`) REFERENCES `assessment_aitrainingworkflow` (`id`),
  CONSTRAINT `ff4ddecc43bd06c0d85785a61e955133` FOREIGN KEY (`trainingexample_id`) REFERENCES `assessment_trainingexample` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_uuid` varchar(128) NOT NULL,
  `scored_at` datetime(6) NOT NULL,
  `scorer_id` varchar(40) NOT NULL,
  `score_type` varchar(2) NOT NULL,
  `feedback` longtext NOT NULL,
  `rubric_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assessment_assessment_ab5b2b73` (`submission_uuid`),
  KEY `assessment_assessment_ef4c53ff` (`scored_at`),
  KEY `assessment_assessment_7b0042c0` (`scorer_id`),
  KEY `assessment_assessment_8980b7ae` (`rubric_id`),
  CONSTRAINT `assessment_as_rubric_id_7997f01dcbd05633_fk_assessment_rubric_id` FOREIGN KEY (`rubric_id`) REFERENCES `assessment_rubric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessmentfeedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessmentfeedback` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_uuid` varchar(128) NOT NULL,
  `feedback_text` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_uuid` (`submission_uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessmentfeedback_assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessmentfeedback_assessments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `assessmentfeedback_id` int(11) NOT NULL,
  `assessment_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assessmentfeedback_id` (`assessmentfeedback_id`,`assessment_id`),
  KEY `asses_assessment_id_392d354eca2e0c87_fk_assessment_assessment_id` (`assessment_id`),
  CONSTRAINT `D1fc3fa7cd7be79d20561668a95a9fc1` FOREIGN KEY (`assessmentfeedback_id`) REFERENCES `assessment_assessmentfeedback` (`id`),
  CONSTRAINT `asses_assessment_id_392d354eca2e0c87_fk_assessment_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `assessment_assessment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessmentfeedback_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessmentfeedback_options` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `assessmentfeedback_id` int(11) NOT NULL,
  `assessmentfeedbackoption_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assessmentfeedback_id` (`assessmentfeedback_id`,`assessmentfeedbackoption_id`),
  KEY `cc7028abc88c431df3172c9b2d6422e4` (`assessmentfeedbackoption_id`),
  CONSTRAINT `cba12ac98c4a04d67d5edaa2223f4fe5` FOREIGN KEY (`assessmentfeedback_id`) REFERENCES `assessment_assessmentfeedback` (`id`),
  CONSTRAINT `cc7028abc88c431df3172c9b2d6422e4` FOREIGN KEY (`assessmentfeedbackoption_id`) REFERENCES `assessment_assessmentfeedbackoption` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessmentfeedbackoption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessmentfeedbackoption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `text` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `text` (`text`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_assessmentpart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_assessmentpart` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `feedback` longtext NOT NULL,
  `assessment_id` int(11) NOT NULL,
  `criterion_id` int(11) NOT NULL,
  `option_id` int(11),
  PRIMARY KEY (`id`),
  KEY `asses_assessment_id_1d752290138ce479_fk_assessment_assessment_id` (`assessment_id`),
  KEY `assessment_assessmentpart_385b00a3` (`criterion_id`),
  KEY `assessment_assessmentpart_28df3725` (`option_id`),
  CONSTRAINT `asse_option_id_2508a14feeabf4ce_fk_assessment_criterionoption_id` FOREIGN KEY (`option_id`) REFERENCES `assessment_criterionoption` (`id`),
  CONSTRAINT `asses_assessment_id_1d752290138ce479_fk_assessment_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `assessment_assessment` (`id`),
  CONSTRAINT `assessm_criterion_id_2061f2359fd292bf_fk_assessment_criterion_id` FOREIGN KEY (`criterion_id`) REFERENCES `assessment_criterion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_criterion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_criterion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `label` varchar(100) NOT NULL,
  `order_num` int(10) unsigned NOT NULL,
  `prompt` longtext NOT NULL,
  `rubric_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assessment_criterion_8980b7ae` (`rubric_id`),
  CONSTRAINT `assessment_cr_rubric_id_30b7422eb7f191cd_fk_assessment_rubric_id` FOREIGN KEY (`rubric_id`) REFERENCES `assessment_rubric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_criterionoption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_criterionoption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_num` int(10) unsigned NOT NULL,
  `points` int(10) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `label` varchar(100) NOT NULL,
  `explanation` longtext NOT NULL,
  `criterion_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assessm_criterion_id_4d0f74d959b454af_fk_assessment_criterion_id` (`criterion_id`),
  CONSTRAINT `assessm_criterion_id_4d0f74d959b454af_fk_assessment_criterion_id` FOREIGN KEY (`criterion_id`) REFERENCES `assessment_criterion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_peerworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_peerworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  `submission_uuid` varchar(128) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `grading_completed_at` datetime(6) DEFAULT NULL,
  `cancelled_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_uuid` (`submission_uuid`),
  KEY `assessment_peerworkflow_30a811f6` (`student_id`),
  KEY `assessment_peerworkflow_82bfda79` (`item_id`),
  KEY `assessment_peerworkflow_ea134da7` (`course_id`),
  KEY `assessment_peerworkflow_fde81f11` (`created_at`),
  KEY `assessment_peerworkflow_4430a679` (`completed_at`),
  KEY `assessment_peerworkflow_85d183d8` (`grading_completed_at`),
  KEY `assessment_peerworkflow_740da1db` (`cancelled_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_peerworkflowitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_peerworkflowitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_uuid` varchar(128) NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `scored` tinyint(1) NOT NULL,
  `assessment_id` int(11) DEFAULT NULL,
  `author_id` int(11) NOT NULL,
  `scorer_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `asses_assessment_id_15cadfae90ddcc2a_fk_assessment_assessment_id` (`assessment_id`),
  KEY `assessm_author_id_1948f89dea6d2b5f_fk_assessment_peerworkflow_id` (`author_id`),
  KEY `assessm_scorer_id_2d803ee2d52c0e2c_fk_assessment_peerworkflow_id` (`scorer_id`),
  KEY `assessment_peerworkflowitem_ab5b2b73` (`submission_uuid`),
  KEY `assessment_peerworkflowitem_ff1ae11b` (`started_at`),
  CONSTRAINT `asses_assessment_id_15cadfae90ddcc2a_fk_assessment_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `assessment_assessment` (`id`),
  CONSTRAINT `assessm_author_id_1948f89dea6d2b5f_fk_assessment_peerworkflow_id` FOREIGN KEY (`author_id`) REFERENCES `assessment_peerworkflow` (`id`),
  CONSTRAINT `assessm_scorer_id_2d803ee2d52c0e2c_fk_assessment_peerworkflow_id` FOREIGN KEY (`scorer_id`) REFERENCES `assessment_peerworkflow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_rubric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_rubric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_hash` varchar(40) NOT NULL,
  `structure_hash` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_hash` (`content_hash`),
  KEY `assessment_rubric_873e9e2d` (`structure_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_staffworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_staffworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scorer_id` varchar(40) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `submission_uuid` varchar(128) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `grading_completed_at` datetime(6) DEFAULT NULL,
  `grading_started_at` datetime(6) DEFAULT NULL,
  `cancelled_at` datetime(6) DEFAULT NULL,
  `assessment` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_uuid` (`submission_uuid`),
  KEY `assessment_staffworkflow_7b0042c0` (`scorer_id`),
  KEY `assessment_staffworkflow_ea134da7` (`course_id`),
  KEY `assessment_staffworkflow_82bfda79` (`item_id`),
  KEY `assessment_staffworkflow_fde81f11` (`created_at`),
  KEY `assessment_staffworkflow_85d183d8` (`grading_completed_at`),
  KEY `assessment_staffworkflow_0af9deae` (`grading_started_at`),
  KEY `assessment_staffworkflow_740da1db` (`cancelled_at`),
  KEY `assessment_staffworkflow_5096c410` (`assessment`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_studenttrainingworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_studenttrainingworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_uuid` varchar(128) NOT NULL,
  `student_id` varchar(40) NOT NULL,
  `item_id` varchar(128) NOT NULL,
  `course_id` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_uuid` (`submission_uuid`),
  KEY `assessment_studenttrainingworkflow_30a811f6` (`student_id`),
  KEY `assessment_studenttrainingworkflow_82bfda79` (`item_id`),
  KEY `assessment_studenttrainingworkflow_ea134da7` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_studenttrainingworkflowitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_studenttrainingworkflowitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_num` int(10) unsigned NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `training_example_id` int(11) NOT NULL,
  `workflow_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assessment_studenttrainingwork_workflow_id_484e930feb86ad74_uniq` (`workflow_id`,`order_num`),
  KEY `assessment_studenttrainingworkflowitem_9cc97abc` (`training_example_id`),
  KEY `assessment_studenttrainingworkflowitem_846c77cf` (`workflow_id`),
  CONSTRAINT `D74ce3e30635de397fef41ac869640c7` FOREIGN KEY (`training_example_id`) REFERENCES `assessment_trainingexample` (`id`),
  CONSTRAINT `f9c080ebc7ad16394edda963ed3f280f` FOREIGN KEY (`workflow_id`) REFERENCES `assessment_studenttrainingworkflow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_trainingexample`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_trainingexample` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `raw_answer` longtext NOT NULL,
  `content_hash` varchar(40) NOT NULL,
  `rubric_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_hash` (`content_hash`),
  KEY `assessment_tr_rubric_id_33664d383bafcaaa_fk_assessment_rubric_id` (`rubric_id`),
  CONSTRAINT `assessment_tr_rubric_id_33664d383bafcaaa_fk_assessment_rubric_id` FOREIGN KEY (`rubric_id`) REFERENCES `assessment_rubric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `assessment_trainingexample_options_selected`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessment_trainingexample_options_selected` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trainingexample_id` int(11) NOT NULL,
  `criterionoption_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `trainingexample_id` (`trainingexample_id`,`criterionoption_id`),
  KEY `D0b4a450eed0c653d223e489254ed8a1` (`criterionoption_id`),
  CONSTRAINT `D0b4a450eed0c653d223e489254ed8a1` FOREIGN KEY (`criterionoption_id`) REFERENCES `assessment_criterionoption` (`id`),
  CONSTRAINT `ae406d6687690bb9277287984729cfd8` FOREIGN KEY (`trainingexample_id`) REFERENCES `assessment_trainingexample` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
  KEY `auth_group__permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id` (`permission_id`),
  CONSTRAINT `auth_group__permission_id_1f49ccbbdc69d2fc_fk_auth_permission_id` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permission_group_id_689710a9a73b7457_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  CONSTRAINT `auth__content_type_id_508cf46651277a81_fk_django_content_type_id` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=824 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_registration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_registration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `activation_key` varchar(32) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `activation_key` (`activation_key`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `auth_registration_user_id_734af68780d0cf34_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
  KEY `auth_user_groups_group_id_33ac548dcf5f8e37_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_33ac548dcf5f8e37_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_4b5ed4ffdb8fd9b0_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
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
  KEY `auth_user_u_permission_id_384b62483d7071f0_fk_auth_permission_id` (`permission_id`),
  CONSTRAINT `auth_user_u_permission_id_384b62483d7071f0_fk_auth_permission_id` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissi_user_id_7f0938558328534a_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_userprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `meta` longtext NOT NULL,
  `courseware` varchar(255) NOT NULL,
  `language` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `year_of_birth` int(11) DEFAULT NULL,
  `gender` varchar(6) DEFAULT NULL,
  `level_of_education` varchar(6) DEFAULT NULL,
  `mailing_address` longtext,
  `city` longtext,
  `country` varchar(2) DEFAULT NULL,
  `goals` longtext,
  `allow_certificate` tinyint(1) NOT NULL,
  `bio` varchar(3000) DEFAULT NULL,
  `profile_image_uploaded_at` datetime(6) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `auth_userprofile_b068931c` (`name`),
  KEY `auth_userprofile_8512ae7d` (`language`),
  KEY `auth_userprofile_d5189de0` (`location`),
  KEY `auth_userprofile_8939d49d` (`year_of_birth`),
  KEY `auth_userprofile_cc90f191` (`gender`),
  KEY `auth_userprofile_a895faa8` (`level_of_education`),
  CONSTRAINT `auth_userprofile_user_id_4c194f9b5650ad70_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `badges_badgeassertion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `badges_badgeassertion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `data` longtext NOT NULL,
  `backend` varchar(50) NOT NULL,
  `image_url` varchar(200) NOT NULL,
  `assertion_url` varchar(200) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `created` datetime(6) NOT NULL,
  `badge_class_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `badges_badgeassertion_e2fa5388` (`created`),
  KEY `badges_badgeassertion_c389e456` (`badge_class_id`),
  KEY `badges_badgeassertion_e8701ad4` (`user_id`),
  CONSTRAINT `badges_b_badge_class_id_3a4a16cb833201e8_fk_badges_badgeclass_id` FOREIGN KEY (`badge_class_id`) REFERENCES `badges_badgeclass` (`id`),
  CONSTRAINT `badges_badgeassertion_user_id_14233cdefee1055a_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `badges_badgeclass`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `badges_badgeclass` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `slug` varchar(255) NOT NULL,
  `issuing_component` varchar(50) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `criteria` longtext NOT NULL,
  `mode` varchar(100) NOT NULL,
  `image` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `badges_badgeclass_slug_7fe9eac3bca91f16_uniq` (`slug`,`issuing_component`,`course_id`),
  KEY `badges_badgeclass_2dbcba41` (`slug`),
  KEY `badges_badgeclass_a57403f2` (`issuing_component`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `badges_coursecompleteimageconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `badges_coursecompleteimageconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mode` varchar(125) NOT NULL,
  `icon` varchar(100) NOT NULL,
  `default` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mode` (`mode`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `badges_courseeventbadgesconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `badges_courseeventbadgesconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `courses_completed` longtext NOT NULL,
  `courses_enrolled` longtext NOT NULL,
  `course_groups` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `badges_courseeven_changed_by_id_50986a94d73238b9_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `badges_courseeven_changed_by_id_50986a94d73238b9_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bookmarks_bookmark`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bookmarks_bookmark` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `usage_key` varchar(255) NOT NULL,
  `path` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  `xblock_cache_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bookmarks_bookmark_user_id_7059f67cddd52c9a_uniq` (`user_id`,`usage_key`),
  KEY `bookmarks_bookmark_c8235886` (`course_key`),
  KEY `bookmarks_bookmark_4a93f0de` (`usage_key`),
  KEY `bookmarks_bookmark_d452fbf6` (`xblock_cache_id`),
  CONSTRAINT `boo_xblock_cache_id_22d48842487ba2d2_fk_bookmarks_xblockcache_id` FOREIGN KEY (`xblock_cache_id`) REFERENCES `bookmarks_xblockcache` (`id`),
  CONSTRAINT `bookmarks_bookmark_user_id_33914fa9accf01cb_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bookmarks_xblockcache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bookmarks_xblockcache` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `usage_key` varchar(255) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `paths` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usage_key` (`usage_key`),
  KEY `bookmarks_xblockcache_c8235886` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `branding_brandingapiconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `branding_brandingapiconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `branding_branding_changed_by_id_127fa63777522d05_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `branding_branding_changed_by_id_127fa63777522d05_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `branding_brandinginfoconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `branding_brandinginfoconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `configuration` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `branding_branding_changed_by_id_298e4241fae118cc_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `branding_branding_changed_by_id_298e4241fae118cc_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_bulkemailflag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_bulkemailflag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `require_course_email_auth` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bulk_email_bulkem_changed_by_id_67960d6511f876aa_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `bulk_email_bulkem_changed_by_id_67960d6511f876aa_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
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
  UNIQUE KEY `course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_courseemail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_courseemail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `slug` varchar(128) NOT NULL,
  `subject` varchar(128) NOT NULL,
  `html_message` longtext,
  `text_message` longtext,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `to_option` varchar(64) NOT NULL,
  `template_name` varchar(255) DEFAULT NULL,
  `from_addr` varchar(255) DEFAULT NULL,
  `sender_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bulk_email_courseemai_sender_id_37be3a6322a26640_fk_auth_user_id` (`sender_id`),
  KEY `bulk_email_courseemail_2dbcba41` (`slug`),
  KEY `bulk_email_courseemail_ea134da7` (`course_id`),
  CONSTRAINT `bulk_email_courseemai_sender_id_37be3a6322a26640_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_courseemailtemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_courseemailtemplate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `html_template` longtext,
  `plain_template` longtext,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bulk_email_optout`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bulk_email_optout` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bulk_email_optout_user_id_7710cb544aafa8a_uniq` (`user_id`,`course_id`),
  KEY `bulk_email_optout_ea134da7` (`course_id`),
  CONSTRAINT `bulk_email_optout_user_id_5d6e4a037bcf14bd_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ccx_ccxfieldoverride`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ccx_ccxfieldoverride` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `location` varchar(255) NOT NULL,
  `field` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `ccx_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ccx_ccxfieldoverride_ccx_id_432b832e71334ab2_uniq` (`ccx_id`,`location`,`field`),
  KEY `ccx_ccxfieldoverride_d5189de0` (`location`),
  KEY `ccx_ccxfieldoverride_5b9c1ccd` (`ccx_id`),
  CONSTRAINT `ccx_ccxfield_ccx_id_9266d91ee561fcc_fk_ccx_customcourseforedx_id` FOREIGN KEY (`ccx_id`) REFERENCES `ccx_customcourseforedx` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ccx_customcourseforedx`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ccx_customcourseforedx` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `coach_id` int(11) NOT NULL,
  `structure_json` longtext,
  PRIMARY KEY (`id`),
  KEY `ccx_customcourseforedx_coach_id_ad6ec0656b3bae_fk_auth_user_id` (`coach_id`),
  KEY `ccx_customcourseforedx_ea134da7` (`course_id`),
  CONSTRAINT `ccx_customcourseforedx_coach_id_ad6ec0656b3bae_fk_auth_user_id` FOREIGN KEY (`coach_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ccxcon_ccxcon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ccxcon_ccxcon` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `url` varchar(200) NOT NULL,
  `oauth_client_id` varchar(255) NOT NULL,
  `oauth_client_secret` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url` (`url`)
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
  `date_done` datetime(6) NOT NULL,
  `traceback` longtext,
  `hidden` tinyint(1) NOT NULL,
  `meta` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `celery_taskmeta_662f707d` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(255) NOT NULL,
  `result` longtext NOT NULL,
  `date_done` datetime(6) NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`),
  KEY `celery_tasksetmeta_662f707d` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificategenerationconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificategenerationconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_cert_changed_by_id_2a1d896cdbd5fec5_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `certificates_cert_changed_by_id_2a1d896cdbd5fec5_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificategenerationcoursesetting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificategenerationcoursesetting` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_certificategenerationcoursesetting_c8235886` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificategenerationhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificategenerationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `is_regeneration` tinyint(1) NOT NULL,
  `generated_by_id` int(11) NOT NULL,
  `instructor_task_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_ce_generated_by_id_4679598e2d7d6e10_fk_auth_user_id` (`generated_by_id`),
  KEY `D794923145b81064c232a4d0bfe79880` (`instructor_task_id`),
  CONSTRAINT `D794923145b81064c232a4d0bfe79880` FOREIGN KEY (`instructor_task_id`) REFERENCES `instructor_task_instructortask` (`id`),
  CONSTRAINT `certificates_ce_generated_by_id_4679598e2d7d6e10_fk_auth_user_id` FOREIGN KEY (`generated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificatehtmlviewconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificatehtmlviewconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `configuration` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_cert_changed_by_id_1de6cf549bca749b_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `certificates_cert_changed_by_id_1de6cf549bca749b_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificateinvalidation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificateinvalidation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `notes` longtext,
  `active` tinyint(1) NOT NULL,
  `generated_certificate_id` int(11) NOT NULL,
  `invalidated_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fa0dc816ca8028cd93e5f2289d405d87` (`generated_certificate_id`),
  KEY `certificates__invalidated_by_id_5198db337fb56b7b_fk_auth_user_id` (`invalidated_by_id`),
  CONSTRAINT `certificates__invalidated_by_id_5198db337fb56b7b_fk_auth_user_id` FOREIGN KEY (`invalidated_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `fa0dc816ca8028cd93e5f2289d405d87` FOREIGN KEY (`generated_certificate_id`) REFERENCES `certificates_generatedcertificate` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificatetemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificatetemplate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `template` longtext NOT NULL,
  `organization_id` int(11) DEFAULT NULL,
  `course_key` varchar(255) DEFAULT NULL,
  `mode` varchar(125) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificates_certificatetem_organization_id_f0c7bfd32b374fb_uniq` (`organization_id`,`course_key`,`mode`),
  KEY `certificates_certificatetemplate_26b2345e` (`organization_id`),
  KEY `certificates_certificatetemplate_c8235886` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificatetemplateasset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificatetemplateasset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `asset` varchar(255) NOT NULL,
  `asset_slug` varchar(255),
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_slug` (`asset_slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_certificatewhitelist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_certificatewhitelist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `whitelist` tinyint(1) NOT NULL,
  `created` datetime(6) NOT NULL,
  `notes` longtext,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_certificat_user_id_50b0bc90075a5407_fk_auth_user_id` (`user_id`),
  CONSTRAINT `certificates_certificat_user_id_50b0bc90075a5407_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_examplecertificate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_examplecertificate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `description` varchar(255) NOT NULL,
  `uuid` varchar(255) NOT NULL,
  `access_key` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `template` varchar(255) NOT NULL,
  `status` varchar(255) NOT NULL,
  `error_reason` longtext,
  `download_url` varchar(255) DEFAULT NULL,
  `example_cert_set_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `certificates_examplecertificate_91685379` (`access_key`),
  KEY `certificates_examplecertificate_c9ee6da7` (`example_cert_set_id`),
  CONSTRAINT `D5ceae87b49ed6ab15ace7b6f1c01c35` FOREIGN KEY (`example_cert_set_id`) REFERENCES `certificates_examplecertificateset` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_examplecertificateset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_examplecertificateset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_examplecertificateset_c8235886` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `certificates_generatedcertificate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `certificates_generatedcertificate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `verify_uuid` varchar(32) NOT NULL,
  `download_uuid` varchar(32) NOT NULL,
  `download_url` varchar(128) NOT NULL,
  `grade` varchar(5) NOT NULL,
  `key` varchar(32) NOT NULL,
  `distinction` tinyint(1) NOT NULL,
  `status` varchar(32) NOT NULL,
  `mode` varchar(32) NOT NULL,
  `name` varchar(255) NOT NULL,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `error_reason` varchar(512) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificates_generatedcertificate_user_id_552a0fa6f7d3f7e8_uniq` (`user_id`,`course_id`),
  KEY `certificates_generatedcertific_verify_uuid_1b5a14bb83c471ff_uniq` (`verify_uuid`),
  CONSTRAINT `certificates_generatedc_user_id_77ed5f7a53121815_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `commerce_commerceconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `commerce_commerceconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `checkout_on_ecommerce_service` tinyint(1) NOT NULL,
  `single_course_checkout_page` varchar(255) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `commerce_commerce_changed_by_id_7441951d1c97c1d7_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `commerce_commerce_changed_by_id_7441951d1c97c1d7_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `contentserver_cdnuseragentsconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contentserver_cdnuseragentsconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `cdn_user_agents` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `contentserver_cdn_changed_by_id_36fe2b67b2c7f0ba_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `contentserver_cdn_changed_by_id_36fe2b67b2c7f0ba_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `contentserver_courseassetcachettlconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contentserver_courseassetcachettlconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `cache_ttl` int(10) unsigned NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `contentserver_cou_changed_by_id_3b5e5ff6c6df495d_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `contentserver_cou_changed_by_id_3b5e5ff6c6df495d_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `contentstore_pushnotificationconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contentstore_pushnotificationconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `contentstore_push_changed_by_id_72c47af098f7f8b1_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `contentstore_push_changed_by_id_72c47af098f7f8b1_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `contentstore_videouploadconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contentstore_videouploadconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `profile_whitelist` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `contentstore_vide_changed_by_id_17a489d0a46d9a4b_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `contentstore_vide_changed_by_id_17a489d0a46d9a4b_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `cors_csrf_xdomainproxyconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cors_csrf_xdomainproxyconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `whitelist` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cors_csrf_xdomain_changed_by_id_31e52cd1bcef52c4_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `cors_csrf_xdomain_changed_by_id_31e52cd1bcef52c4_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `corsheaders_corsmodel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `corsheaders_corsmodel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cors` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_action_state_coursererunstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_action_state_coursererunstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `action` varchar(100) NOT NULL,
  `state` varchar(50) NOT NULL,
  `should_display` tinyint(1) NOT NULL,
  `message` varchar(1000) NOT NULL,
  `source_course_key` varchar(255) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `created_user_id` int(11) DEFAULT NULL,
  `updated_user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_action_state_coursereruns_course_key_cf5da77ed3032d6_uniq` (`course_key`,`action`),
  KEY `course_action_s_created_user_id_7f53088ef8dccd0b_fk_auth_user_id` (`created_user_id`),
  KEY `course_action_s_updated_user_id_4fab18012332c9a4_fk_auth_user_id` (`updated_user_id`),
  KEY `course_action_state_coursererunstate_c8235886` (`course_key`),
  KEY `course_action_state_coursererunstate_418c5509` (`action`),
  KEY `course_action_state_coursererunstate_a9bd7343` (`source_course_key`),
  CONSTRAINT `course_action_s_created_user_id_7f53088ef8dccd0b_fk_auth_user_id` FOREIGN KEY (`created_user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `course_action_s_updated_user_id_4fab18012332c9a4_fk_auth_user_id` FOREIGN KEY (`updated_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_creators_coursecreator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_creators_coursecreator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state_changed` datetime(6) NOT NULL,
  `state` varchar(24) NOT NULL,
  `note` varchar(512) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `course_creators_coursec_user_id_46ea06ad28f0be3b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_cohortmembership`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_cohortmembership` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `course_user_group_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_groups_cohortmembership_user_id_395bddd0389ed7da_uniq` (`user_id`,`course_id`),
  KEY `course_groups_cohortmembership_6e438ee3` (`course_user_group_id`),
  KEY `course_groups_cohortmembership_e8701ad4` (`user_id`),
  CONSTRAINT `D004e77c965054d46217a8bd48bcaec8` FOREIGN KEY (`course_user_group_id`) REFERENCES `course_groups_courseusergroup` (`id`),
  CONSTRAINT `course_groups_cohortmem_user_id_15d408bf736398bf_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_coursecohort`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_coursecohort` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `assignment_type` varchar(20) NOT NULL,
  `course_user_group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_user_group_id` (`course_user_group_id`),
  CONSTRAINT `D339c347a8fab561c2e92ea09f250df8` FOREIGN KEY (`course_user_group_id`) REFERENCES `course_groups_courseusergroup` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_coursecohortssettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_coursecohortssettings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `is_cohorted` tinyint(1) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `cohorted_discussions` longtext,
  `always_cohort_inline_discussions` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`)
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
  UNIQUE KEY `course_groups_courseusergroup_name_63f7511804c52f38_uniq` (`name`,`course_id`),
  KEY `course_groups_courseusergroup_ea134da7` (`course_id`)
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
  KEY `course_groups_courseuse_user_id_7b26cdeaeb621a93_fk_auth_user_id` (`user_id`),
  CONSTRAINT `course_groups_courseuse_user_id_7b26cdeaeb621a93_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `db746f642b1b8232920506afe242fe6b` FOREIGN KEY (`courseusergroup_id`) REFERENCES `course_groups_courseusergroup` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_groups_courseusergrouppartitiongroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_groups_courseusergrouppartitiongroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partition_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `course_user_group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_user_group_id` (`course_user_group_id`),
  CONSTRAINT `D1516b3811dd6dd500bfae054d6fdc92` FOREIGN KEY (`course_user_group_id`) REFERENCES `course_groups_courseusergroup` (`id`)
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
  `currency` varchar(8) NOT NULL,
  `expiration_datetime` datetime(6) DEFAULT NULL,
  `expiration_date` date DEFAULT NULL,
  `suggested_prices` varchar(255) NOT NULL,
  `description` longtext,
  `sku` varchar(255) DEFAULT NULL,
  `expiration_datetime_is_explicit` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_modes_coursemode_course_id_6fbb1796ace558b4_uniq` (`course_id`,`mode_slug`,`currency`),
  KEY `course_modes_coursemode_ea134da7` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_modes_coursemodeexpirationconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_modes_coursemodeexpirationconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `verification_window` bigint(20) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `course_modes_cour_changed_by_id_4d31fab2bbe98b89_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `course_modes_cour_changed_by_id_4d31fab2bbe98b89_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_modes_coursemodesarchive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_modes_coursemodesarchive` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `mode_slug` varchar(100) NOT NULL,
  `mode_display_name` varchar(255) NOT NULL,
  `min_price` int(11) NOT NULL,
  `suggested_prices` varchar(255) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `expiration_date` date DEFAULT NULL,
  `expiration_datetime` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `course_modes_coursemodesarchive_ea134da7` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_overviews_courseoverview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_overviews_courseoverview` (
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `version` int(11) NOT NULL,
  `id` varchar(255) NOT NULL,
  `_location` varchar(255) NOT NULL,
  `display_name` longtext,
  `display_number_with_default` longtext NOT NULL,
  `display_org_with_default` longtext NOT NULL,
  `start` datetime(6) DEFAULT NULL,
  `end` datetime(6) DEFAULT NULL,
  `advertised_start` longtext,
  `course_image_url` longtext NOT NULL,
  `social_sharing_url` longtext,
  `end_of_course_survey_url` longtext,
  `certificates_display_behavior` longtext,
  `certificates_show_before_end` tinyint(1) NOT NULL,
  `cert_html_view_enabled` tinyint(1) NOT NULL,
  `has_any_active_web_certificate` tinyint(1) NOT NULL,
  `cert_name_short` longtext NOT NULL,
  `cert_name_long` longtext NOT NULL,
  `lowest_passing_grade` decimal(5,2) DEFAULT NULL,
  `days_early_for_beta` double DEFAULT NULL,
  `mobile_available` tinyint(1) NOT NULL,
  `visible_to_staff_only` tinyint(1) NOT NULL,
  `_pre_requisite_courses_json` longtext NOT NULL,
  `enrollment_start` datetime(6) DEFAULT NULL,
  `enrollment_end` datetime(6) DEFAULT NULL,
  `enrollment_domain` longtext,
  `invitation_only` tinyint(1) NOT NULL,
  `max_student_enrollments_allowed` int(11) DEFAULT NULL,
  `announcement` datetime(6),
  `catalog_visibility` longtext,
  `course_video_url` longtext,
  `effort` longtext,
  `short_description` longtext,
  `org` longtext NOT NULL,
  `self_paced` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_overviews_courseoverviewimageconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_overviews_courseoverviewimageconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `small_width` int(11) NOT NULL,
  `small_height` int(11) NOT NULL,
  `large_width` int(11) NOT NULL,
  `large_height` int(11) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `course_overviews__changed_by_id_54b19ba1c134af6a_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `course_overviews__changed_by_id_54b19ba1c134af6a_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_overviews_courseoverviewimageset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_overviews_courseoverviewimageset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `small_url` longtext NOT NULL,
  `large_url` longtext NOT NULL,
  `course_overview_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_overview_id` (`course_overview_id`),
  CONSTRAINT `D47baf904f8952eb0e1fafefd558a718` FOREIGN KEY (`course_overview_id`) REFERENCES `course_overviews_courseoverview` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_overviews_courseoverviewtab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_overviews_courseoverviewtab` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tab_id` varchar(50) NOT NULL,
  `course_overview_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D298658de1d4c8777e046eed658fc94e` (`course_overview_id`),
  CONSTRAINT `D298658de1d4c8777e046eed658fc94e` FOREIGN KEY (`course_overview_id`) REFERENCES `course_overviews_courseoverview` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_overviews_courseoverview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_overviews_courseoverview` (
  `id` varchar(255) NOT NULL,
  `_location` varchar(255) NOT NULL,
  `display_name` longtext,
  `display_number_with_default` longtext NOT NULL,
  `display_org_with_default` longtext NOT NULL,
  `start` datetime DEFAULT NULL,
  `end` datetime DEFAULT NULL,
  `advertised_start` longtext,
  `course_image_url` longtext NOT NULL,
  `facebook_url` longtext,
  `social_sharing_url` longtext,
  `end_of_course_survey_url` longtext,
  `certificates_display_behavior` longtext,
  `certificates_show_before_end` tinyint(1) NOT NULL,
  `has_any_active_web_certificate` tinyint(1) NOT NULL,
  `cert_name_short` longtext NOT NULL,
  `cert_name_long` longtext NOT NULL,
  `lowest_passing_grade` decimal(5,2) NOT NULL,
  `mobile_available` tinyint(1) NOT NULL,
  `visible_to_staff_only` tinyint(1) NOT NULL,
  `_pre_requisite_courses_json` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `course_structures_coursestructure`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_structures_coursestructure` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `structure_json` longtext,
  `discussion_id_map_json` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `coursetalk_coursetalkwidgetconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `coursetalk_coursetalkwidgetconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `platform_key` varchar(50) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `coursetalk_course_changed_by_id_18bd24020c1b37d5_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `coursetalk_course_changed_by_id_18bd24020c1b37d5_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_offlinecomputedgrade`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_offlinecomputedgrade` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `updated` datetime(6) NOT NULL,
  `gradeset` longtext,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_offlinecomputedgrade_user_id_46133bbd0926078f_uniq` (`user_id`,`course_id`),
  KEY `courseware_offlinecomputedgrade_ea134da7` (`course_id`),
  KEY `courseware_offlinecomputedgrade_e2fa5388` (`created`),
  KEY `courseware_offlinecomputedgrade_0f81d52e` (`updated`),
  CONSTRAINT `courseware_offlinecompu_user_id_66bbccbf945dfd56_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_offlinecomputedgradelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_offlinecomputedgradelog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `seconds` int(11) NOT NULL,
  `nstudents` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `courseware_offlinecomputedgradelog_ea134da7` (`course_id`),
  KEY `courseware_offlinecomputedgradelog_e2fa5388` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_studentfieldoverride`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_studentfieldoverride` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `field` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `student_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_studentfieldoverride_course_id_39dd7eaeac5623d2_uniq` (`course_id`,`field`,`location`,`student_id`),
  KEY `courseware_studentfi_student_id_70e7c0f5a4f91b65_fk_auth_user_id` (`student_id`),
  KEY `courseware_studentfieldoverride_ea134da7` (`course_id`),
  KEY `courseware_studentfieldoverride_d5189de0` (`location`),
  CONSTRAINT `courseware_studentfi_student_id_70e7c0f5a4f91b65_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_studentmodule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_studentmodule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `module_type` varchar(32) NOT NULL,
  `module_id` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `state` longtext,
  `grade` double DEFAULT NULL,
  `max_grade` double DEFAULT NULL,
  `done` varchar(8) NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `student_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_studentmodule_student_id_635d77aea1256de5_uniq` (`student_id`,`module_id`,`course_id`),
  KEY `courseware_studentmodule_82bd5515` (`module_type`),
  KEY `courseware_studentmodule_c9799665` (`module_id`),
  KEY `courseware_studentmodule_ea134da7` (`course_id`),
  KEY `courseware_studentmodule_de6a20aa` (`grade`),
  KEY `courseware_studentmodule_6b2ded51` (`done`),
  KEY `courseware_studentmodule_e2fa5388` (`created`),
  KEY `courseware_studentmodule_9ae73c65` (`modified`),
  CONSTRAINT `courseware_studentmo_student_id_57005a9a97046500_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_studentmodulehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_studentmodulehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `version` varchar(255) DEFAULT NULL,
  `created` datetime(6) NOT NULL,
  `state` longtext,
  `grade` double DEFAULT NULL,
  `max_grade` double DEFAULT NULL,
  `student_module_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D45b867f7277556beb93bff02eba5f03` (`student_module_id`),
  KEY `courseware_studentmodulehistory_2af72f10` (`version`),
  KEY `courseware_studentmodulehistory_e2fa5388` (`created`),
  CONSTRAINT `D45b867f7277556beb93bff02eba5f03` FOREIGN KEY (`student_module_id`) REFERENCES `courseware_studentmodule` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmodulestudentinfofield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmodulestudentinfofield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `value` longtext NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `student_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmodulestudentinfofi_student_id_33f2f772c49db067_uniq` (`student_id`,`field_name`),
  KEY `courseware_xmodulestudentinfofield_73f329f1` (`field_name`),
  KEY `courseware_xmodulestudentinfofield_e2fa5388` (`created`),
  KEY `courseware_xmodulestudentinfofield_9ae73c65` (`modified`),
  CONSTRAINT `courseware_xmodulestu_student_id_fb4c5883b541e28_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmodulestudentprefsfield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmodulestudentprefsfield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `value` longtext NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `module_type` varchar(64) NOT NULL,
  `student_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmodulestudentprefsf_student_id_2a5d275498b7a407_uniq` (`student_id`,`module_type`,`field_name`),
  KEY `courseware_xmodulestudentprefsfield_73f329f1` (`field_name`),
  KEY `courseware_xmodulestudentprefsfield_e2fa5388` (`created`),
  KEY `courseware_xmodulestudentprefsfield_9ae73c65` (`modified`),
  KEY `courseware_xmodulestudentprefsfield_82bd5515` (`module_type`),
  CONSTRAINT `courseware_xmodulest_student_id_48b35c14cbc17185_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courseware_xmoduleuserstatesummaryfield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `courseware_xmoduleuserstatesummaryfield` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_name` varchar(64) NOT NULL,
  `value` longtext NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `usage_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courseware_xmoduleuserstatesummar_usage_id_5cc7ed48d6e2e021_uniq` (`usage_id`,`field_name`),
  KEY `courseware_xmoduleuserstatesummaryfield_73f329f1` (`field_name`),
  KEY `courseware_xmoduleuserstatesummaryfield_e2fa5388` (`created`),
  KEY `courseware_xmoduleuserstatesummaryfield_9ae73c65` (`modified`),
  KEY `courseware_xmoduleuserstatesummaryfield_0528eb2a` (`usage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credentials_credentialsapiconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credentials_credentialsapiconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `internal_service_url` varchar(200) NOT NULL,
  `public_service_url` varchar(200) NOT NULL,
  `enable_learner_issuance` tinyint(1) NOT NULL,
  `enable_studio_authoring` tinyint(1) NOT NULL,
  `cache_ttl` int(10) unsigned NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `credentials_crede_changed_by_id_273a2e6b0649c861_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `credentials_crede_changed_by_id_273a2e6b0649c861_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `cache_ttl` int(10) unsigned NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `credit_creditconf_changed_by_id_6270a800475f6694_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `credit_creditconf_changed_by_id_6270a800475f6694_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditcourse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditcourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_key` varchar(255) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_key` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_crediteligibility`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_crediteligibility` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `username` varchar(255) NOT NULL,
  `deadline` datetime(6) NOT NULL,
  `course_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `credit_crediteligibility_username_936cb16677e83e_uniq` (`username`,`course_id`),
  KEY `credit_cred_course_id_4218adeba258bf8b_fk_credit_creditcourse_id` (`course_id`),
  KEY `credit_crediteligibility_14c4b06b` (`username`),
  CONSTRAINT `credit_cred_course_id_4218adeba258bf8b_fk_credit_creditcourse_id` FOREIGN KEY (`course_id`) REFERENCES `credit_creditcourse` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditprovider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditprovider` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `provider_id` varchar(255) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `enable_integration` tinyint(1) NOT NULL,
  `provider_url` varchar(200) NOT NULL,
  `provider_status_url` varchar(200) NOT NULL,
  `provider_description` longtext NOT NULL,
  `fulfillment_instructions` longtext,
  `eligibility_email_message` longtext NOT NULL,
  `receipt_email_message` longtext NOT NULL,
  `thumbnail_url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider_id` (`provider_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditrequest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `uuid` varchar(32) NOT NULL,
  `username` varchar(255) NOT NULL,
  `parameters` longtext NOT NULL,
  `status` varchar(255) NOT NULL,
  `course_id` int(11) NOT NULL,
  `provider_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `credit_creditrequest_username_4f61c10bb0d67c01_uniq` (`username`,`course_id`,`provider_id`),
  KEY `credit_cred_course_id_578c5f1124002bab_fk_credit_creditcourse_id` (`course_id`),
  KEY `credit_c_provider_id_f2973cc3e38a483_fk_credit_creditprovider_id` (`provider_id`),
  KEY `credit_creditrequest_14c4b06b` (`username`),
  CONSTRAINT `credit_c_provider_id_f2973cc3e38a483_fk_credit_creditprovider_id` FOREIGN KEY (`provider_id`) REFERENCES `credit_creditprovider` (`id`),
  CONSTRAINT `credit_cred_course_id_578c5f1124002bab_fk_credit_creditcourse_id` FOREIGN KEY (`course_id`) REFERENCES `credit_creditcourse` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditrequirement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditrequirement` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `namespace` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `order` int(10) unsigned NOT NULL,
  `criteria` longtext NOT NULL,
  `active` tinyint(1) NOT NULL,
  `course_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `credit_creditrequirement_namespace_33039c83b3e69b8_uniq` (`namespace`,`name`,`course_id`),
  KEY `credit_cred_course_id_1c8fb9ebd295ae19_fk_credit_creditcourse_id` (`course_id`),
  CONSTRAINT `credit_cred_course_id_1c8fb9ebd295ae19_fk_credit_creditcourse_id` FOREIGN KEY (`course_id`) REFERENCES `credit_creditcourse` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_creditrequirementstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_creditrequirementstatus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `username` varchar(255) NOT NULL,
  `status` varchar(32) NOT NULL,
  `reason` longtext NOT NULL,
  `requirement_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `credit_creditrequirementstatus_username_67dcb69ebf779e3b_uniq` (`username`,`requirement_id`),
  KEY `c_requirement_id_3896aa6db214f84a_fk_credit_creditrequirement_id` (`requirement_id`),
  KEY `credit_creditrequirementstatus_14c4b06b` (`username`),
  CONSTRAINT `c_requirement_id_3896aa6db214f84a_fk_credit_creditrequirement_id` FOREIGN KEY (`requirement_id`) REFERENCES `credit_creditrequirement` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_historicalcreditrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_historicalcreditrequest` (
  `id` int(11) NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `uuid` varchar(32) NOT NULL,
  `username` varchar(255) NOT NULL,
  `parameters` longtext NOT NULL,
  `status` varchar(255) NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `course_id` int(11) DEFAULT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `provider_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`history_id`),
  KEY `credit_historic_history_user_id_52a9922f26a69e7e_fk_auth_user_id` (`history_user_id`),
  KEY `credit_historicalcreditrequest_b80bb774` (`id`),
  KEY `credit_historicalcreditrequest_ef7c876f` (`uuid`),
  KEY `credit_historicalcreditrequest_14c4b06b` (`username`),
  CONSTRAINT `credit_historic_history_user_id_52a9922f26a69e7e_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_historicalcreditrequirementstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_historicalcreditrequirementstatus` (
  `id` int(11) NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `username` varchar(255) NOT NULL,
  `status` varchar(32) NOT NULL,
  `reason` longtext NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `requirement_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`history_id`),
  KEY `credit_historic_history_user_id_72b045b9192495cc_fk_auth_user_id` (`history_user_id`),
  KEY `credit_historicalcreditrequirementstatus_b80bb774` (`id`),
  KEY `credit_historicalcreditrequirementstatus_14c4b06b` (`username`),
  CONSTRAINT `credit_historic_history_user_id_72b045b9192495cc_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `credit_historicalcreditrequirementstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `credit_historicalcreditrequirementstatus` (
  `id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `username` varchar(255) NOT NULL,
  `status` varchar(32) NOT NULL,
  `reason` longtext NOT NULL,
  `requirement_id` int(11) DEFAULT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `history_type` varchar(1) NOT NULL,
  PRIMARY KEY (`history_id`),
  KEY `credit_historicalcreditrequirementstatus_4a5fc416` (`id`),
  KEY `credit_historicalcreditrequirementstatus_f774835d` (`username`),
  KEY `credit_historicalcreditrequirementstatus_99a85f32` (`requirement_id`),
  KEY `credit_historicalcreditrequirementstatus_e1a0ea2a` (`history_user_id`),
  CONSTRAINT `history_user_id_refs_id_9342f9b4` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `requirement_id_refs_id_b49b13a7` FOREIGN KEY (`requirement_id`) REFERENCES `credit_creditrequirement` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `dark_lang_darklangconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dark_lang_darklangconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `released_languages` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dark_lang_darklan_changed_by_id_7e1defb1121d58b8_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `dark_lang_darklan_changed_by_id_7e1defb1121d58b8_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `djang_content_type_id_697914295151027a_fk_django_content_type_id` (`content_type_id`),
  KEY `django_admin_log_user_id_52fdd58701c5f563_fk_auth_user_id` (`user_id`),
  CONSTRAINT `djang_content_type_id_697914295151027a_fk_django_content_type_id` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_52fdd58701c5f563_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
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
  UNIQUE KEY `permission_id` (`permission_id`,`role_id`),
  KEY `django_role_id_558412c96ef7ba87_fk_django_comment_client_role_id` (`role_id`),
  CONSTRAINT `D4e9a4067c1db9041491363f5e032121` FOREIGN KEY (`permission_id`) REFERENCES `django_comment_client_permission` (`name`),
  CONSTRAINT `django_role_id_558412c96ef7ba87_fk_django_comment_client_role_id` FOREIGN KEY (`role_id`) REFERENCES `django_comment_client_role` (`id`)
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
  KEY `django_comment_client_role_ea134da7` (`course_id`)
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
  UNIQUE KEY `role_id` (`role_id`,`user_id`),
  KEY `django_comment_client_r_user_id_139843e7dcf77368_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_comment_client_r_user_id_139843e7dcf77368_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_role_id_75cf4005dc1fb11d_fk_django_comment_client_role_id` FOREIGN KEY (`role_id`) REFERENCES `django_comment_client_role` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_45f3b1d93ec8c61c_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=274 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=155 DEFAULT CHARSET=utf8;
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
  `claimed_id` longtext NOT NULL,
  `display_id` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_openid_auth_user_user_id_136119e72782e2cf_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_openid_auth_user_user_id_136119e72782e2cf_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_de54fa62` (`expire_date`)
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
  `expires` datetime(6) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime(6) DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime(6) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `djc_interval_id_20cfc1cad060dfad_fk_djcelery_intervalschedule_id` (`interval_id`),
  KEY `djcel_crontab_id_1d8228f5b44b680a_fk_djcelery_crontabschedule_id` (`crontab_id`),
  CONSTRAINT `djc_interval_id_20cfc1cad060dfad_fk_djcelery_intervalschedule_id` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`),
  CONSTRAINT `djcel_crontab_id_1d8228f5b44b680a_fk_djcelery_crontabschedule_id` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime(6) NOT NULL,
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
  `tstamp` datetime(6) NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime(6) DEFAULT NULL,
  `expires` datetime(6) DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `retries` int(11) NOT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `djcelery_t_worker_id_30050731b1c3d3d9_fk_djcelery_workerstate_id` (`worker_id`),
  KEY `djcelery_taskstate_9ed39e2e` (`state`),
  KEY `djcelery_taskstate_b068931c` (`name`),
  KEY `djcelery_taskstate_863bb2ee` (`tstamp`),
  KEY `djcelery_taskstate_662f707d` (`hidden`),
  CONSTRAINT `djcelery_t_worker_id_30050731b1c3d3d9_fk_djcelery_workerstate_id` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `djcelery_workerstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  KEY `djcelery_workerstate_f129901a` (`last_heartbeat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `edxval_coursevideo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edxval_coursevideo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `video_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `edxval_coursevideo_course_id_42cecee05cff2d8c_uniq` (`course_id`,`video_id`),
  KEY `edxval_coursevideo_b58b747e` (`video_id`),
  CONSTRAINT `edxval_coursevideo_video_id_68b2969f352edd03_fk_edxval_video_id` FOREIGN KEY (`video_id`) REFERENCES `edxval_video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `edxval_encodedvideo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edxval_encodedvideo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `url` varchar(200) NOT NULL,
  `file_size` int(10) unsigned NOT NULL,
  `bitrate` int(10) unsigned NOT NULL,
  `profile_id` int(11) NOT NULL,
  `video_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `edxval_encodedvideo_83a0eb3f` (`profile_id`),
  KEY `edxval_encodedvideo_b58b747e` (`video_id`),
  CONSTRAINT `edxval_encodedv_profile_id_484a111092acafb3_fk_edxval_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `edxval_profile` (`id`),
  CONSTRAINT `edxval_encodedvideo_video_id_56934bca09fc3b13_fk_edxval_video_id` FOREIGN KEY (`video_id`) REFERENCES `edxval_video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `edxval_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edxval_profile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `profile_name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `profile_name` (`profile_name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `edxval_subtitle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edxval_subtitle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `fmt` varchar(20) NOT NULL,
  `language` varchar(8) NOT NULL,
  `content` longtext NOT NULL,
  `video_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `edxval_subtitle_76314543` (`fmt`),
  KEY `edxval_subtitle_8512ae7d` (`language`),
  KEY `edxval_subtitle_b58b747e` (`video_id`),
  CONSTRAINT `edxval_subtitle_video_id_5fabb0e154dda720_fk_edxval_video_id` FOREIGN KEY (`video_id`) REFERENCES `edxval_video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `edxval_video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edxval_video` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `edx_video_id` varchar(100) NOT NULL,
  `client_video_id` varchar(255) NOT NULL,
  `duration` double NOT NULL,
  `status` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `edx_video_id` (`edx_video_id`),
  KEY `edxval_video_8d63c4f7` (`client_video_id`),
  KEY `edxval_video_9acb4454` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_country`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_country` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `country` varchar(2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `country` (`country`)
) ENGINE=InnoDB AUTO_INCREMENT=251 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_countryaccessrule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_countryaccessrule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `rule_type` varchar(255) NOT NULL,
  `country_id` int(11) NOT NULL,
  `restricted_course_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `embargo_countryaccess_restricted_course_id_6f340c36c633cb0a_uniq` (`restricted_course_id`,`country_id`),
  KEY `embargo_countr_country_id_6244ff9d9c405c6e_fk_embargo_country_id` (`country_id`),
  KEY `embargo_countryaccessrule_77607676` (`restricted_course_id`),
  CONSTRAINT `d140f72cce132ba9230b3ff66d8761ad` FOREIGN KEY (`restricted_course_id`) REFERENCES `embargo_restrictedcourse` (`id`),
  CONSTRAINT `embargo_countr_country_id_6244ff9d9c405c6e_fk_embargo_country_id` FOREIGN KEY (`country_id`) REFERENCES `embargo_country` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_courseaccessrulehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_courseaccessrulehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `snapshot` longtext,
  PRIMARY KEY (`id`),
  KEY `embargo_courseaccessrulehistory_d7e6d55b` (`timestamp`),
  KEY `embargo_courseaccessrulehistory_c8235886` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_embargoedcourse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_embargoedcourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `embargoed` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_embargoedstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_embargoedstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `embargoed_countries` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `embargo_embargoeds_changed_by_id_7e30811d0e5008b_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `embargo_embargoeds_changed_by_id_7e30811d0e5008b_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_ipfilter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_ipfilter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `whitelist` longtext NOT NULL,
  `blacklist` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `embargo_ipfilter_changed_by_id_5c820bfac889ea81_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `embargo_ipfilter_changed_by_id_5c820bfac889ea81_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `embargo_restrictedcourse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `embargo_restrictedcourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_key` varchar(255) NOT NULL,
  `enroll_msg_key` varchar(255) NOT NULL,
  `access_msg_key` varchar(255) NOT NULL,
  `disable_access_check` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_key` (`course_key`)
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
  `internal_password` varchar(31) NOT NULL,
  `dtcreated` datetime(6) NOT NULL,
  `dtsignup` datetime(6) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_auth_externalauthmap_external_id_7f035ef8bc4d313e_uniq` (`external_id`,`external_domain`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `external_auth_externalauthmap_0e684294` (`external_id`),
  KEY `external_auth_externalauthmap_630a0308` (`external_domain`),
  KEY `external_auth_externalauthmap_e9425fc5` (`external_email`),
  KEY `external_auth_externalauthmap_c9555995` (`external_name`),
  CONSTRAINT `external_auth_externala_user_id_644e7779f2d52b9a_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
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
  `created` datetime(6) DEFAULT NULL,
  `updated` datetime(6) NOT NULL,
  `subtasks` longtext NOT NULL,
  `requester_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `instructor_task_in_requester_id_3383acfe2fe42391_fk_auth_user_id` (`requester_id`),
  KEY `instructor_task_instructortask_5361aa34` (`task_type`),
  KEY `instructor_task_instructortask_ea134da7` (`course_id`),
  KEY `instructor_task_instructortask_a2903537` (`task_key`),
  KEY `instructor_task_instructortask_57746cc8` (`task_id`),
  KEY `instructor_task_instructortask_76980a94` (`task_state`),
  CONSTRAINT `instructor_task_in_requester_id_3383acfe2fe42391_fk_auth_user_id` FOREIGN KEY (`requester_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `lms_xblock_xblockasidesconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lms_xblock_xblockasidesconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `disabled_blocks` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lms_xblock_xblocka_changed_by_id_eabf5ef3e34dfb8_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `lms_xblock_xblocka_changed_by_id_eabf5ef3e34dfb8_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_historicalmicrositeorganizationmapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_historicalmicrositeorganizationmapping` (
  `id` int(11) NOT NULL,
  `organization` varchar(63) NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `microsite_id` int(11),
  PRIMARY KEY (`history_id`),
  KEY `microsite_confi_history_user_id_40846fe04877dd35_fk_auth_user_id` (`history_user_id`),
  KEY `microsite_configuration_historicalmicrositeorganizationmappi1219` (`id`),
  KEY `microsite_configuration_historicalmicrositeorganizationmappi74d9` (`organization`),
  KEY `microsite_configuration_historicalmicrositeorganizationmappi5a96` (`microsite_id`),
  CONSTRAINT `microsite_confi_history_user_id_40846fe04877dd35_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_historicalmicrositetemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_historicalmicrositetemplate` (
  `id` int(11) NOT NULL,
  `template_uri` varchar(255) NOT NULL,
  `template` longtext NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `microsite_id` int(11),
  PRIMARY KEY (`history_id`),
  KEY `microsite_confi_history_user_id_53e1b0dcb708d6ef_fk_auth_user_id` (`history_user_id`),
  KEY `microsite_configuration_historicalmicrositetemplate_b80bb774` (`id`),
  KEY `microsite_configuration_historicalmicrositetemplate_a8b249ec` (`template_uri`),
  KEY `microsite_configuration_historicalmicrositetemplate_c9cd58ae` (`microsite_id`),
  CONSTRAINT `microsite_confi_history_user_id_53e1b0dcb708d6ef_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_microsite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_microsite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(63) NOT NULL,
  `values` longtext NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  UNIQUE KEY `site_id` (`site_id`),
  CONSTRAINT `microsite_configuratio_site_id_3ebe20a76de5aa4_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_micrositehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_micrositehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `key` varchar(63) NOT NULL,
  `values` longtext NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `microsite_configurati_site_id_6977a04d3625a533_fk_django_site_id` (`site_id`),
  CONSTRAINT `microsite_configurati_site_id_6977a04d3625a533_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_micrositeorganizationmapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_micrositeorganizationmapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `organization` varchar(63) NOT NULL,
  `microsite_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `organization` (`organization`),
  KEY `D1c5d7dbbb2cde12ce18b38d46f71ee0` (`microsite_id`),
  CONSTRAINT `D1c5d7dbbb2cde12ce18b38d46f71ee0` FOREIGN KEY (`microsite_id`) REFERENCES `microsite_configuration_microsite` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `microsite_configuration_micrositetemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `microsite_configuration_micrositetemplate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `template_uri` varchar(255) NOT NULL,
  `template` longtext NOT NULL,
  `microsite_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `microsite_configuration_micros_microsite_id_80b3f3616d2e317_uniq` (`microsite_id`,`template_uri`),
  KEY `microsite_configuration_micrositetemplate_a8b249ec` (`template_uri`),
  CONSTRAINT `D4919cbc5f1414d3de93aa9ec9aa48f3` FOREIGN KEY (`microsite_id`) REFERENCES `microsite_configuration_microsite` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `milestones_coursecontentmilestone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones_coursecontentmilestone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `content_id` varchar(255) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `milestone_id` int(11) NOT NULL,
  `milestone_relationship_type_id` int(11) NOT NULL,
  `requirements` varchar(255),
  PRIMARY KEY (`id`),
  UNIQUE KEY `milestones_coursecontentmileston_course_id_68d1457cd52d6dff_uniq` (`course_id`,`content_id`,`milestone_id`),
  KEY `milestones_coursecontentmilestone_ea134da7` (`course_id`),
  KEY `milestones_coursecontentmilestone_e14f02ad` (`content_id`),
  KEY `milestones_coursecontentmilestone_dbb5cd1e` (`milestone_id`),
  KEY `milestones_coursecontentmilestone_db6866e3` (`milestone_relationship_type_id`),
  KEY `milestones_coursecontentmilestone_active_39b5c645fa33bfee_uniq` (`active`),
  CONSTRAINT `D84e404851bc6d6b9fe0d60955e8729c` FOREIGN KEY (`milestone_relationship_type_id`) REFERENCES `milestones_milestonerelationshiptype` (`id`),
  CONSTRAINT `milesto_milestone_id_73b6eddde5b205a8_fk_milestones_milestone_id` FOREIGN KEY (`milestone_id`) REFERENCES `milestones_milestone` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `milestones_coursemilestone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones_coursemilestone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `milestone_id` int(11) NOT NULL,
  `milestone_relationship_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `milestones_coursemilestone_course_id_5a06e10579eab3b7_uniq` (`course_id`,`milestone_id`),
  KEY `milestones_coursemilestone_ea134da7` (`course_id`),
  KEY `milestones_coursemilestone_dbb5cd1e` (`milestone_id`),
  KEY `milestones_coursemilestone_db6866e3` (`milestone_relationship_type_id`),
  KEY `milestones_coursemilestone_active_5c3a925f8cc4bde2_uniq` (`active`),
  CONSTRAINT `D69536d0d313008147c5daf5341090e1` FOREIGN KEY (`milestone_relationship_type_id`) REFERENCES `milestones_milestonerelationshiptype` (`id`),
  CONSTRAINT `milesto_milestone_id_284153799c54d7d8_fk_milestones_milestone_id` FOREIGN KEY (`milestone_id`) REFERENCES `milestones_milestone` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `milestones_milestone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones_milestone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `namespace` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `milestones_milestone_namespace_460a2f6943016c0b_uniq` (`namespace`,`name`),
  KEY `milestones_milestone_89801e9e` (`namespace`),
  KEY `milestones_milestone_b068931c` (`name`),
  KEY `milestones_milestone_active_1182ba3c09d42c35_uniq` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `milestones_milestonerelationshiptype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones_milestonerelationshiptype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `name` varchar(25) NOT NULL,
  `description` longtext NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `milestones_usermilestone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones_usermilestone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `source` longtext NOT NULL,
  `collected` datetime(6) DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  `milestone_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `milestones_usermilestone_user_id_10206aa452468351_uniq` (`user_id`,`milestone_id`),
  KEY `milesto_milestone_id_4fe38e3e9994f15c_fk_milestones_milestone_id` (`milestone_id`),
  KEY `milestones_usermilestone_e8701ad4` (`user_id`),
  KEY `milestones_usermilestone_active_1827f467fe87a8ea_uniq` (`active`),
  CONSTRAINT `milesto_milestone_id_4fe38e3e9994f15c_fk_milestones_milestone_id` FOREIGN KEY (`milestone_id`) REFERENCES `milestones_milestone` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `mobile_api_appversionconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mobile_api_appversionconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `platform` varchar(50) NOT NULL,
  `version` varchar(50) NOT NULL,
  `major_version` int(11) NOT NULL,
  `minor_version` int(11) NOT NULL,
  `patch_version` int(11) NOT NULL,
  `expire_at` datetime(6) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mobile_api_appversionconfig_platform_d34993f68d46008_uniq` (`platform`,`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `mobile_api_mobileapiconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mobile_api_mobileapiconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `video_profiles` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mobile_api_mobile_changed_by_id_439d2c27670d0fc4_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `mobile_api_mobile_changed_by_id_439d2c27670d0fc4_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notes_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notes_note` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `uri` varchar(255) NOT NULL,
  `text` longtext NOT NULL,
  `quote` longtext NOT NULL,
  `range_start` varchar(2048) NOT NULL,
  `range_start_offset` int(11) NOT NULL,
  `range_end` varchar(2048) NOT NULL,
  `range_end_offset` int(11) NOT NULL,
  `tags` longtext NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `updated` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notes_note_user_id_2aa1ff88fd937cb3_fk_auth_user_id` (`user_id`),
  KEY `notes_note_ea134da7` (`course_id`),
  KEY `notes_note_9305b73d` (`uri`),
  KEY `notes_note_e2fa5388` (`created`),
  KEY `notes_note_0f81d52e` (`updated`),
  CONSTRAINT `notes_note_user_id_2aa1ff88fd937cb3_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_notification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `url` varchar(200) DEFAULT NULL,
  `is_viewed` tinyint(1) NOT NULL,
  `is_emailed` tinyint(1) NOT NULL,
  `created` datetime(6) NOT NULL,
  `subscription_id` int(11),
  PRIMARY KEY (`id`),
  KEY `notify_notification_ef42673f` (`subscription_id`),
  CONSTRAINT `D48032390695e0699e92b8d7ccdbff7e` FOREIGN KEY (`subscription_id`) REFERENCES `notify_subscription` (`subscription_id`)
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
  KEY `notif_content_type_id_181f055892581fd8_fk_django_content_type_id` (`content_type_id`),
  CONSTRAINT `notif_content_type_id_181f055892581fd8_fk_django_content_type_id` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `interval` smallint(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notify_settings_user_id_14e062dc3d4345b3_fk_auth_user_id` (`user_id`),
  CONSTRAINT `notify_settings_user_id_14e062dc3d4345b3_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `notify_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notify_subscription` (
  `subscription_id` int(11) NOT NULL AUTO_INCREMENT,
  `object_id` varchar(64) DEFAULT NULL,
  `send_emails` tinyint(1) NOT NULL,
  `notification_type_id` varchar(128) NOT NULL,
  `settings_id` int(11) NOT NULL,
  PRIMARY KEY (`subscription_id`),
  KEY `a2462650bbefc26547210b80dec61069` (`notification_type_id`),
  KEY `notify_subscr_settings_id_64d594d127e8ca95_fk_notify_settings_id` (`settings_id`),
  CONSTRAINT `a2462650bbefc26547210b80dec61069` FOREIGN KEY (`notification_type_id`) REFERENCES `notify_notificationtype` (`key`),
  CONSTRAINT `notify_subscr_settings_id_64d594d127e8ca95_fk_notify_settings_id` FOREIGN KEY (`settings_id`) REFERENCES `notify_settings` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_accesstoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_accesstoken` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(255) NOT NULL,
  `expires` datetime(6) NOT NULL,
  `scope` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth2_accesstoken_94a08da1` (`token`),
  KEY `oauth2_accesstoken_2bfe9d72` (`client_id`),
  KEY `oauth2_accesstoken_e8701ad4` (`user_id`),
  CONSTRAINT `oauth2_accesstoke_client_id_20c73b03a7c139a2_fk_oauth2_client_id` FOREIGN KEY (`client_id`) REFERENCES `oauth2_client` (`id`),
  CONSTRAINT `oauth2_accesstoken_user_id_7a865c7085722378_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_client` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `url` varchar(200) NOT NULL,
  `redirect_uri` varchar(200) NOT NULL,
  `client_id` varchar(255) NOT NULL,
  `client_secret` varchar(255) NOT NULL,
  `client_type` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth2_client_user_id_2b47284bbd512fe1_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth2_client_user_id_2b47284bbd512fe1_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_grant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_grant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(255) NOT NULL,
  `expires` datetime(6) NOT NULL,
  `redirect_uri` varchar(255) NOT NULL,
  `scope` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth2_grant_client_id_fbfc174fbc856af_fk_oauth2_client_id` (`client_id`),
  KEY `oauth2_grant_user_id_3de96a461bb76819_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth2_grant_client_id_fbfc174fbc856af_fk_oauth2_client_id` FOREIGN KEY (`client_id`) REFERENCES `oauth2_client` (`id`),
  CONSTRAINT `oauth2_grant_user_id_3de96a461bb76819_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_provider_accesstoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_provider_accesstoken` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(255) NOT NULL,
  `expires` datetime(6) NOT NULL,
  `scope` longtext NOT NULL,
  `application_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `D5ac3019ee1c474fd85718b015e3d3a1` (`application_id`),
  KEY `oauth2_provider_accesstoken_94a08da1` (`token`),
  KEY `oauth2_provider_accesst_user_id_5e2f004fdebea22d_fk_auth_user_id` (`user_id`),
  CONSTRAINT `D5ac3019ee1c474fd85718b015e3d3a1` FOREIGN KEY (`application_id`) REFERENCES `oauth2_provider_application` (`id`),
  CONSTRAINT `oauth2_provider_accesst_user_id_5e2f004fdebea22d_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_provider_application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_provider_application` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` varchar(100) NOT NULL,
  `redirect_uris` longtext NOT NULL,
  `client_type` varchar(32) NOT NULL,
  `authorization_grant_type` varchar(32) NOT NULL,
  `client_secret` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  `skip_authorization` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `client_id` (`client_id`),
  KEY `oauth2_provider_application_9d667c2b` (`client_secret`),
  KEY `oauth2_provider_applica_user_id_7fa13387c260b798_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth2_provider_applica_user_id_7fa13387c260b798_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_provider_grant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_provider_grant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(255) NOT NULL,
  `expires` datetime(6) NOT NULL,
  `redirect_uri` varchar(255) NOT NULL,
  `scope` longtext NOT NULL,
  `application_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D6b2a4f1402d4f338b690c38b795830a` (`application_id`),
  KEY `oauth2_provider_grant_user_id_3111344894d452da_fk_auth_user_id` (`user_id`),
  KEY `oauth2_provider_grant_c1336794` (`code`),
  CONSTRAINT `D6b2a4f1402d4f338b690c38b795830a` FOREIGN KEY (`application_id`) REFERENCES `oauth2_provider_application` (`id`),
  CONSTRAINT `oauth2_provider_grant_user_id_3111344894d452da_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_provider_refreshtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_provider_refreshtoken` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(255) NOT NULL,
  `access_token_id` int(11) NOT NULL,
  `application_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `access_token_id` (`access_token_id`),
  KEY `d3e264ceec355cabed6ff9976fc42a06` (`application_id`),
  KEY `oauth2_provider_refresh_user_id_3f695b639cfbc9a3_fk_auth_user_id` (`user_id`),
  KEY `oauth2_provider_refreshtoken_94a08da1` (`token`),
  CONSTRAINT `b58d9cb3b93afb36b11b7741bf1bcc1a` FOREIGN KEY (`access_token_id`) REFERENCES `oauth2_provider_accesstoken` (`id`),
  CONSTRAINT `d3e264ceec355cabed6ff9976fc42a06` FOREIGN KEY (`application_id`) REFERENCES `oauth2_provider_application` (`id`),
  CONSTRAINT `oauth2_provider_refresh_user_id_3f695b639cfbc9a3_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_provider_trustedclient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_provider_trustedclient` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth2_provider_tr_client_id_bb96ea0be42c00a_fk_oauth2_client_id` (`client_id`),
  CONSTRAINT `oauth2_provider_tr_client_id_bb96ea0be42c00a_fk_oauth2_client_id` FOREIGN KEY (`client_id`) REFERENCES `oauth2_client` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth2_refreshtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_refreshtoken` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(255) NOT NULL,
  `expired` tinyint(1) NOT NULL,
  `access_token_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `access_token_id` (`access_token_id`),
  KEY `oauth2_refreshtok_client_id_2f55036ac9aa614e_fk_oauth2_client_id` (`client_id`),
  KEY `oauth2_refreshtoken_user_id_acecf94460b787c_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth2__access_token_id_f99377d503a000b_fk_oauth2_accesstoken_id` FOREIGN KEY (`access_token_id`) REFERENCES `oauth2_accesstoken` (`id`),
  CONSTRAINT `oauth2_refreshtok_client_id_2f55036ac9aa614e_fk_oauth2_client_id` FOREIGN KEY (`client_id`) REFERENCES `oauth2_client` (`id`),
  CONSTRAINT `oauth2_refreshtoken_user_id_acecf94460b787c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth_provider_consumer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth_provider_consumer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `key` varchar(256) NOT NULL,
  `secret` varchar(16) NOT NULL,
  `status` smallint(6) NOT NULL,
  `xauth_allowed` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth_provider_consumer_user_id_4f22b60d2b258006_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth_provider_consumer_user_id_4f22b60d2b258006_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth_provider_nonce`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth_provider_nonce` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token_key` varchar(32) NOT NULL,
  `consumer_key` varchar(256) NOT NULL,
  `key` varchar(255) NOT NULL,
  `timestamp` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth_provider_nonce_d7e6d55b` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth_provider_scope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth_provider_scope` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `url` longtext NOT NULL,
  `is_readonly` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `oauth_provider_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth_provider_token` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(32) DEFAULT NULL,
  `secret` varchar(16) DEFAULT NULL,
  `token_type` smallint(6) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `verifier` varchar(10) NOT NULL,
  `callback` varchar(2083) DEFAULT NULL,
  `callback_confirmed` tinyint(1) NOT NULL,
  `consumer_id` int(11) NOT NULL,
  `scope_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth_consumer_id_1b9915b5bcf1ee5b_fk_oauth_provider_consumer_id` (`consumer_id`),
  KEY `oauth_provi_scope_id_459821b6fecbc02a_fk_oauth_provider_scope_id` (`scope_id`),
  KEY `oauth_provider_token_user_id_588adbcffc892186_fk_auth_user_id` (`user_id`),
  CONSTRAINT `oauth_consumer_id_1b9915b5bcf1ee5b_fk_oauth_provider_consumer_id` FOREIGN KEY (`consumer_id`) REFERENCES `oauth_provider_consumer` (`id`),
  CONSTRAINT `oauth_provi_scope_id_459821b6fecbc02a_fk_oauth_provider_scope_id` FOREIGN KEY (`scope_id`) REFERENCES `oauth_provider_scope` (`id`),
  CONSTRAINT `oauth_provider_token_user_id_588adbcffc892186_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `organizations_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `organizations_organization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `name` varchar(255) NOT NULL,
  `short_name` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `logo` varchar(255) DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `organizations_organization_b068931c` (`name`),
  KEY `organizations_organization_4698bac7` (`short_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `organizations_organizationcourse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `organizations_organizationcourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `organization_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `organizations_organizationcourse_course_id_3f0149776c0495ff_uniq` (`course_id`,`organization_id`),
  KEY `a7b04b16eba98e518fbe21d390bd8e3e` (`organization_id`),
  KEY `organizations_organizationcourse_ea134da7` (`course_id`),
  CONSTRAINT `a7b04b16eba98e518fbe21d390bd8e3e` FOREIGN KEY (`organization_id`) REFERENCES `organizations_organization` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexam` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `content_id` varchar(255) NOT NULL,
  `external_id` varchar(255) DEFAULT NULL,
  `exam_name` longtext NOT NULL,
  `time_limit_mins` int(11) NOT NULL,
  `due_date` datetime(6) DEFAULT NULL,
  `is_proctored` tinyint(1) NOT NULL,
  `is_practice_exam` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `hide_after_due` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proctoring_proctoredexam_course_id_7d8ab189323890c0_uniq` (`course_id`,`content_id`),
  KEY `proctoring_proctoredexam_ea134da7` (`course_id`),
  KEY `proctoring_proctoredexam_e14f02ad` (`content_id`),
  KEY `proctoring_proctoredexam_0e684294` (`external_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamreviewpolicy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamreviewpolicy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `review_policy` longtext NOT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `set_by_user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D32bab97500954b362d3f768dd89b6da` (`proctored_exam_id`),
  KEY `proctoring_proct_set_by_user_id_75a66580aa44cd84_fk_auth_user_id` (`set_by_user_id`),
  CONSTRAINT `D32bab97500954b362d3f768dd89b6da` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proct_set_by_user_id_75a66580aa44cd84_fk_auth_user_id` FOREIGN KEY (`set_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamreviewpolicyhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamreviewpolicyhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `original_id` int(11) NOT NULL,
  `review_policy` longtext NOT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `set_by_user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `d9965d8af87bebd0587414ca1ba4826f` (`proctored_exam_id`),
  KEY `proctoring_procto_set_by_user_id_31fae610848d90f_fk_auth_user_id` (`set_by_user_id`),
  KEY `proctoring_proctoredexamreviewpolicyhistory_524b09d0` (`original_id`),
  CONSTRAINT `d9965d8af87bebd0587414ca1ba4826f` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_procto_set_by_user_id_31fae610848d90f_fk_auth_user_id` FOREIGN KEY (`set_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamsoftwaresecurereview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamsoftwaresecurereview` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `attempt_code` varchar(255) NOT NULL,
  `review_status` varchar(255) NOT NULL,
  `raw_data` longtext NOT NULL,
  `video_url` longtext NOT NULL,
  `exam_id` int(11) DEFAULT NULL,
  `reviewed_by_id` int(11) DEFAULT NULL,
  `student_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proctoring_proctoredexamsoftw_attempt_code_69b9866a54964afb_uniq` (`attempt_code`),
  KEY `proctori_exam_id_635059f5fe2cc392_fk_proctoring_proctoredexam_id` (`exam_id`),
  KEY `proctoring_proct_reviewed_by_id_4cff67b7de094f65_fk_auth_user_id` (`reviewed_by_id`),
  KEY `proctoring_proctored_student_id_14c182517b0cbb5b_fk_auth_user_id` (`student_id`),
  KEY `proctoring_proctoredexamsoftwaresecurereview_b38e5b0e` (`attempt_code`),
  CONSTRAINT `proctori_exam_id_635059f5fe2cc392_fk_proctoring_proctoredexam_id` FOREIGN KEY (`exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proct_reviewed_by_id_4cff67b7de094f65_fk_auth_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `proctoring_proctored_student_id_14c182517b0cbb5b_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamsoftwaresecurereviewhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamsoftwaresecurereviewhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `attempt_code` varchar(255) NOT NULL,
  `review_status` varchar(255) NOT NULL,
  `raw_data` longtext NOT NULL,
  `video_url` longtext NOT NULL,
  `exam_id` int(11) DEFAULT NULL,
  `reviewed_by_id` int(11) DEFAULT NULL,
  `student_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `proctori_exam_id_73969ae423813477_fk_proctoring_proctoredexam_id` (`exam_id`),
  KEY `proctoring_proct_reviewed_by_id_139568d0bf423998_fk_auth_user_id` (`reviewed_by_id`),
  KEY `proctoring_proctored_student_id_6922ba3b791462d8_fk_auth_user_id` (`student_id`),
  KEY `proctoring_proctoredexamsoftwaresecurereviewhistory_b38e5b0e` (`attempt_code`),
  CONSTRAINT `proctori_exam_id_73969ae423813477_fk_proctoring_proctoredexam_id` FOREIGN KEY (`exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proct_reviewed_by_id_139568d0bf423998_fk_auth_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `proctoring_proctored_student_id_6922ba3b791462d8_fk_auth_user_id` FOREIGN KEY (`student_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamstudentallowance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamstudentallowance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `key` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proctoring_proctoredexamstudentall_user_id_665ed945152c2f60_uniq` (`user_id`,`proctored_exam_id`,`key`),
  KEY `db55b83a7875e70b3a0ebd1f81a898d8` (`proctored_exam_id`),
  CONSTRAINT `db55b83a7875e70b3a0ebd1f81a898d8` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proctoredexam_user_id_a0a0681d4a01661_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamstudentallowancehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamstudentallowancehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `allowance_id` int(11) NOT NULL,
  `key` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D169ec97a7fca1dbf6b0bb2929d41ccc` (`proctored_exam_id`),
  KEY `proctoring_proctoredexa_user_id_68e25e3abb187580_fk_auth_user_id` (`user_id`),
  CONSTRAINT `D169ec97a7fca1dbf6b0bb2929d41ccc` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proctoredexa_user_id_68e25e3abb187580_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamstudentattempt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamstudentattempt` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `last_poll_timestamp` datetime(6) DEFAULT NULL,
  `last_poll_ipaddr` varchar(32) DEFAULT NULL,
  `attempt_code` varchar(255) DEFAULT NULL,
  `external_id` varchar(255) DEFAULT NULL,
  `allowed_time_limit_mins` int(11) NOT NULL,
  `status` varchar(64) NOT NULL,
  `taking_as_proctored` tinyint(1) NOT NULL,
  `is_sample_attempt` tinyint(1) NOT NULL,
  `student_name` varchar(255) NOT NULL,
  `review_policy_id` int(11) DEFAULT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `is_status_acknowledged` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proctoring_proctoredexamstudentatt_user_id_15d13fa8dac316a0_uniq` (`user_id`,`proctored_exam_id`),
  KEY `D5e0a120c32f715bfe04a0a57f399ec0` (`proctored_exam_id`),
  KEY `proctoring_proctoredexamstudentattempt_b38e5b0e` (`attempt_code`),
  KEY `proctoring_proctoredexamstudentattempt_0e684294` (`external_id`),
  CONSTRAINT `D5e0a120c32f715bfe04a0a57f399ec0` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proctoredexa_user_id_633fd8f4f65a0cac_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamstudentattemptcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamstudentattemptcomment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `start_time` int(11) NOT NULL,
  `stop_time` int(11) NOT NULL,
  `duration` int(11) NOT NULL,
  `comment` longtext NOT NULL,
  `status` varchar(255) NOT NULL,
  `review_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `proctoring_proctoredexamstudentattemptcomment_5bd2a989` (`review_id`),
  CONSTRAINT `D596dd9c7d948d9256c2e29e6194b5e7` FOREIGN KEY (`review_id`) REFERENCES `proctoring_proctoredexamsoftwaresecurereview` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `proctoring_proctoredexamstudentattempthistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proctoring_proctoredexamstudentattempthistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `attempt_id` int(11) DEFAULT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `attempt_code` varchar(255) DEFAULT NULL,
  `external_id` varchar(255) DEFAULT NULL,
  `allowed_time_limit_mins` int(11) NOT NULL,
  `status` varchar(64) NOT NULL,
  `taking_as_proctored` tinyint(1) NOT NULL,
  `is_sample_attempt` tinyint(1) NOT NULL,
  `student_name` varchar(255) NOT NULL,
  `review_policy_id` int(11) DEFAULT NULL,
  `last_poll_timestamp` datetime(6) DEFAULT NULL,
  `last_poll_ipaddr` varchar(32) DEFAULT NULL,
  `proctored_exam_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cbccbfd5c4c427541fdce96e77e6bf6c` (`proctored_exam_id`),
  KEY `proctoring_proctoredexa_user_id_59ce75db7c4fc769_fk_auth_user_id` (`user_id`),
  KEY `proctoring_proctoredexamstudentattempthistory_b38e5b0e` (`attempt_code`),
  KEY `proctoring_proctoredexamstudentattempthistory_0e684294` (`external_id`),
  CONSTRAINT `cbccbfd5c4c427541fdce96e77e6bf6c` FOREIGN KEY (`proctored_exam_id`) REFERENCES `proctoring_proctoredexam` (`id`),
  CONSTRAINT `proctoring_proctoredexa_user_id_59ce75db7c4fc769_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `programs_programsapiconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `programs_programsapiconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `internal_service_url` varchar(200) NOT NULL,
  `public_service_url` varchar(200) NOT NULL,
  `api_version_number` int(11) NOT NULL,
  `enable_student_dashboard` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `cache_ttl` int(10) unsigned NOT NULL,
  `authoring_app_css_path` varchar(255) NOT NULL,
  `authoring_app_js_path` varchar(255) NOT NULL,
  `enable_studio_tab` tinyint(1) NOT NULL,
  `enable_certification` tinyint(1) NOT NULL,
  `max_retries` int(10) unsigned NOT NULL,
  `xseries_ad_enabled` tinyint(1) NOT NULL,
  `program_listing_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `programs_programsa_changed_by_id_b7c3b49d5c0dcd3_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `programs_programsa_changed_by_id_b7c3b49d5c0dcd3_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `rss_proxy_whitelistedrssurl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rss_proxy_whitelistedrssurl` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `self_paced_selfpacedconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `self_paced_selfpacedconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `enable_course_home_improvements` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `self_paced_selfpa_changed_by_id_62c0bd4c6725fd15_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `self_paced_selfpa_changed_by_id_62c0bd4c6725fd15_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `reverification_midcoursereverificationwindow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reverification_midcoursereverificationwindow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `reverification_midcoursereverificationwindow_ff48d8e5` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_certificateitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_certificateitem` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  `mode` varchar(50) NOT NULL,
  `course_enrollment_id` int(11) NOT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `D231cb871868cb92e6ed1ee8e53a1bee` (`course_enrollment_id`),
  KEY `shoppingcart_certificateitem_ea134da7` (`course_id`),
  KEY `shoppingcart_certificateitem_15d61712` (`mode`),
  CONSTRAINT `D231cb871868cb92e6ed1ee8e53a1bee` FOREIGN KEY (`course_enrollment_id`) REFERENCES `student_courseenrollment` (`id`),
  CONSTRAINT `s_orderitem_ptr_id_5127313bc5a09762_fk_shoppingcart_orderitem_id` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_coupon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_coupon` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `course_id` varchar(255) NOT NULL,
  `percentage_discount` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `expiration_date` datetime(6) DEFAULT NULL,
  `created_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_coup_created_by_id_625ade1b541f5324_fk_auth_user_id` (`created_by_id`),
  KEY `shoppingcart_coupon_c1336794` (`code`),
  CONSTRAINT `shoppingcart_coup_created_by_id_625ade1b541f5324_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_couponredemption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_couponredemption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `coupon_id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcar_coupon_id_1afa016627ac44bb_fk_shoppingcart_coupon_id` (`coupon_id`),
  KEY `shoppingcart_couponredemption_69dfcb07` (`order_id`),
  KEY `shoppingcart_couponredemption_e8701ad4` (`user_id`),
  CONSTRAINT `shoppingcar_coupon_id_1afa016627ac44bb_fk_shoppingcart_coupon_id` FOREIGN KEY (`coupon_id`) REFERENCES `shoppingcart_coupon` (`id`),
  CONSTRAINT `shoppingcart__order_id_5ba031c3bfaf643a_fk_shoppingcart_order_id` FOREIGN KEY (`order_id`) REFERENCES `shoppingcart_order` (`id`),
  CONSTRAINT `shoppingcart_couponredemp_user_id_f5b814b7d92666_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_courseregcodeitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_courseregcodeitem` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  `mode` varchar(50) NOT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `shoppingcart_courseregcodeitem_ea134da7` (`course_id`),
  KEY `shoppingcart_courseregcodeitem_15d61712` (`mode`),
  CONSTRAINT `s_orderitem_ptr_id_7ca6c1b9c7df7905_fk_shoppingcart_orderitem_id` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_courseregcodeitemannotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_courseregcodeitemannotation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(128) NOT NULL,
  `annotation` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_courseregistrationcode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_courseregistrationcode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `mode_slug` varchar(100) DEFAULT NULL,
  `is_valid` tinyint(1) NOT NULL,
  `created_by_id` int(11) NOT NULL,
  `invoice_id` int(11),
  `order_id` int(11),
  `invoice_item_id` int(11),
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `shoppingcart_cour_created_by_id_11125a9667aa01c9_fk_auth_user_id` (`created_by_id`),
  KEY `shoppingcart_courseregistrationcode_ea134da7` (`course_id`),
  KEY `shoppingcart_courseregistrationcode_f1f5d967` (`invoice_id`),
  KEY `shoppingcart_courseregistrationcode_69dfcb07` (`order_id`),
  KEY `shoppingcart_courseregistrationcode_7a471658` (`invoice_item_id`),
  CONSTRAINT `f040030b6361304bd87eb40c09a82094` FOREIGN KEY (`invoice_item_id`) REFERENCES `shoppingcart_courseregistrationcodeinvoiceitem` (`invoiceitem_ptr_id`),
  CONSTRAINT `shoppingc_invoice_id_422f26bdc7c5cb99_fk_shoppingcart_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `shoppingcart_invoice` (`id`),
  CONSTRAINT `shoppingcart__order_id_279d7e2df3fe6b6a_fk_shoppingcart_order_id` FOREIGN KEY (`order_id`) REFERENCES `shoppingcart_order` (`id`),
  CONSTRAINT `shoppingcart_cour_created_by_id_11125a9667aa01c9_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_courseregistrationcodeinvoiceitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_courseregistrationcodeinvoiceitem` (
  `invoiceitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  PRIMARY KEY (`invoiceitem_ptr_id`),
  KEY `shoppingcart_courseregistrationcodeinvoiceitem_ea134da7` (`course_id`),
  CONSTRAINT `D75797188300cb2dc6a7b16353295aaf` FOREIGN KEY (`invoiceitem_ptr_id`) REFERENCES `shoppingcart_invoiceitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_donation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_donation` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `donation_type` varchar(32) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `shoppingcart_donation_ea134da7` (`course_id`),
  CONSTRAINT `s_orderitem_ptr_id_18caefe119e0bd2f_fk_shoppingcart_orderitem_id` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_donationconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_donationconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_dona_changed_by_id_10ac60a96e315545_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `shoppingcart_dona_changed_by_id_10ac60a96e315545_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_invoice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `company_contact_name` varchar(255) NOT NULL,
  `company_contact_email` varchar(255) NOT NULL,
  `recipient_name` varchar(255) NOT NULL,
  `recipient_email` varchar(255) NOT NULL,
  `address_line_1` varchar(255) NOT NULL,
  `address_line_2` varchar(255) DEFAULT NULL,
  `address_line_3` varchar(255) DEFAULT NULL,
  `city` varchar(255) DEFAULT NULL,
  `state` varchar(255) DEFAULT NULL,
  `zip` varchar(15) DEFAULT NULL,
  `country` varchar(64) DEFAULT NULL,
  `total_amount` double NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `internal_reference` varchar(255) DEFAULT NULL,
  `customer_reference_number` varchar(63) DEFAULT NULL,
  `is_valid` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_invoice_c1007e8a` (`company_name`),
  KEY `shoppingcart_invoice_ea134da7` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_invoicehistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_invoicehistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime(6) NOT NULL,
  `snapshot` longtext NOT NULL,
  `invoice_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingca_invoice_id_e314dc5a906704d_fk_shoppingcart_invoice_id` (`invoice_id`),
  KEY `shoppingcart_invoicehistory_d7e6d55b` (`timestamp`),
  CONSTRAINT `shoppingca_invoice_id_e314dc5a906704d_fk_shoppingcart_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `shoppingcart_invoice` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_invoiceitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_invoiceitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `qty` int(11) NOT NULL,
  `unit_price` decimal(30,2) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `invoice_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_invoiceitem_f1f5d967` (`invoice_id`),
  CONSTRAINT `shoppingc_invoice_id_35828791c8405d01_fk_shoppingcart_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `shoppingcart_invoice` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_invoicetransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_invoicetransaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `amount` decimal(30,2) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `comments` longtext,
  `status` varchar(32) NOT NULL,
  `created_by_id` int(11) NOT NULL,
  `invoice_id` int(11) NOT NULL,
  `last_modified_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_invoi_created_by_id_f5f3d90ce55a145_fk_auth_user_id` (`created_by_id`),
  KEY `shoppingc_invoice_id_66bdbfa6f029288b_fk_shoppingcart_invoice_id` (`invoice_id`),
  KEY `shoppingcar_last_modified_by_id_5e10e433f9576d91_fk_auth_user_id` (`last_modified_by_id`),
  CONSTRAINT `shoppingc_invoice_id_66bdbfa6f029288b_fk_shoppingcart_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `shoppingcart_invoice` (`id`),
  CONSTRAINT `shoppingcar_last_modified_by_id_5e10e433f9576d91_fk_auth_user_id` FOREIGN KEY (`last_modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `shoppingcart_invoi_created_by_id_f5f3d90ce55a145_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_order` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `currency` varchar(8) NOT NULL,
  `status` varchar(32) NOT NULL,
  `purchase_time` datetime(6) DEFAULT NULL,
  `refunded_time` datetime(6) DEFAULT NULL,
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
  `company_name` varchar(255) DEFAULT NULL,
  `company_contact_name` varchar(255) DEFAULT NULL,
  `company_contact_email` varchar(255) DEFAULT NULL,
  `recipient_name` varchar(255) DEFAULT NULL,
  `recipient_email` varchar(255) DEFAULT NULL,
  `customer_reference_number` varchar(63) DEFAULT NULL,
  `order_type` varchar(32) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_order_user_id_4e1f3e3b06ee22a6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `shoppingcart_order_user_id_4e1f3e3b06ee22a6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_orderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_orderitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `status` varchar(32) NOT NULL,
  `qty` int(11) NOT NULL,
  `unit_cost` decimal(30,2) NOT NULL,
  `list_price` decimal(30,2) DEFAULT NULL,
  `line_desc` varchar(1024) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `fulfilled_time` datetime(6) DEFAULT NULL,
  `refund_requested_time` datetime(6) DEFAULT NULL,
  `service_fee` decimal(30,2) NOT NULL,
  `report_comments` longtext NOT NULL,
  `order_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shoppingcart_orderitem_9acb4454` (`status`),
  KEY `shoppingcart_orderitem_3b927c91` (`fulfilled_time`),
  KEY `shoppingcart_orderitem_76ed2946` (`refund_requested_time`),
  KEY `shoppingcart_orderitem_69dfcb07` (`order_id`),
  KEY `shoppingcart_orderitem_e8701ad4` (`user_id`),
  CONSTRAINT `shoppingcart__order_id_325e5347f18743e3_fk_shoppingcart_order_id` FOREIGN KEY (`order_id`) REFERENCES `shoppingcart_order` (`id`),
  CONSTRAINT `shoppingcart_orderitem_user_id_5708ec7aabe24a31_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `shoppingcart_paidcourseregistration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_paidcourseregistration` (
  `orderitem_ptr_id` int(11) NOT NULL,
  `course_id` varchar(128) NOT NULL,
  `mode` varchar(50) NOT NULL,
  `course_enrollment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`orderitem_ptr_id`),
  KEY `D8d681d7e59c2dcf2ea55e7e5e06553d` (`course_enrollment_id`),
  KEY `shoppingcart_paidcourseregistration_ea134da7` (`course_id`),
  KEY `shoppingcart_paidcourseregistration_15d61712` (`mode`),
  CONSTRAINT `D8d681d7e59c2dcf2ea55e7e5e06553d` FOREIGN KEY (`course_enrollment_id`) REFERENCES `student_courseenrollment` (`id`),
  CONSTRAINT `s_orderitem_ptr_id_3c991acc5d644f13_fk_shoppingcart_orderitem_id` FOREIGN KEY (`orderitem_ptr_id`) REFERENCES `shoppingcart_orderitem` (`id`)
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
DROP TABLE IF EXISTS `shoppingcart_registrationcoderedemption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shoppingcart_registrationcoderedemption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `redeemed_at` datetime(6) DEFAULT NULL,
  `course_enrollment_id` int(11) DEFAULT NULL,
  `order_id` int(11) DEFAULT NULL,
  `redeemed_by_id` int(11) NOT NULL,
  `registration_code_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D6654a8efe686d45804b6116dfc6bee1` (`course_enrollment_id`),
  KEY `shoppingcart_r_order_id_752ddc3003afe96_fk_shoppingcart_order_id` (`order_id`),
  KEY `shoppingcart_reg_redeemed_by_id_455df2dd74004fff_fk_auth_user_id` (`redeemed_by_id`),
  KEY `D1ed44c4be114e424571929bce972f54` (`registration_code_id`),
  CONSTRAINT `D1ed44c4be114e424571929bce972f54` FOREIGN KEY (`registration_code_id`) REFERENCES `shoppingcart_courseregistrationcode` (`id`),
  CONSTRAINT `D6654a8efe686d45804b6116dfc6bee1` FOREIGN KEY (`course_enrollment_id`) REFERENCES `student_courseenrollment` (`id`),
  CONSTRAINT `shoppingcart_r_order_id_752ddc3003afe96_fk_shoppingcart_order_id` FOREIGN KEY (`order_id`) REFERENCES `shoppingcart_order` (`id`),
  CONSTRAINT `shoppingcart_reg_redeemed_by_id_455df2dd74004fff_fk_auth_user_id` FOREIGN KEY (`redeemed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `site_configuration_siteconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `site_configuration_siteconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `values` longtext NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `site_id` (`site_id`),
  CONSTRAINT `site_configuration_si_site_id_51c4aa24ab9238cb_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `site_configuration_siteconfigurationhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `site_configuration_siteconfigurationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `values` longtext NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `site_configuration_si_site_id_20c9c1a5f8c3358e_fk_django_site_id` (`site_id`),
  CONSTRAINT `site_configuration_si_site_id_20c9c1a5f8c3358e_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `social_auth_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_url` varchar(255) NOT NULL,
  `handle` varchar(255) NOT NULL,
  `secret` varchar(255) NOT NULL,
  `issued` int(11) NOT NULL,
  `lifetime` int(11) NOT NULL,
  `assoc_type` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `social_auth_code`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_code` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(254) NOT NULL,
  `code` varchar(32) NOT NULL,
  `verified` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_code_email_75f27066d057e3b6_uniq` (`email`,`code`),
  KEY `social_auth_code_c1336794` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `social_auth_nonce`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_nonce` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_url` varchar(255) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `salt` varchar(65) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_nonce_server_url_36601f978463b4_uniq` (`server_url`,`timestamp`,`salt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `social_auth_usersocialauth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_usersocialauth` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider` varchar(32) NOT NULL,
  `uid` varchar(255) NOT NULL,
  `extra_data` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_usersocialauth_provider_2f763109e2c4a1fb_uniq` (`provider`,`uid`),
  KEY `social_auth_usersociala_user_id_193b2d80880502b2_fk_auth_user_id` (`user_id`),
  CONSTRAINT `social_auth_usersociala_user_id_193b2d80880502b2_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `splash_splashconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `splash_splashconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `cookie_name` longtext NOT NULL,
  `cookie_allowed_values` longtext NOT NULL,
  `unaffected_usernames` longtext NOT NULL,
  `unaffected_url_paths` longtext NOT NULL,
  `redirect_url` varchar(200) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `splash_splashconf_changed_by_id_735b38ad8ed19270_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `splash_splashconf_changed_by_id_735b38ad8ed19270_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `static_replace_assetbaseurlconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `static_replace_assetbaseurlconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `base_url` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `static_replace_as_changed_by_id_796c2e5b1bee7027_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `static_replace_as_changed_by_id_796c2e5b1bee7027_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `static_replace_assetexcludedextensionsconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `static_replace_assetexcludedextensionsconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `excluded_extensions` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `static_replace_as_changed_by_id_5885827de4f271dc_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `static_replace_as_changed_by_id_5885827de4f271dc_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `status_coursemessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status_coursemessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_key` varchar(255) NOT NULL,
  `message` longtext,
  `global_message_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `status_coursemessage_c8235886` (`course_key`),
  KEY `status_coursemessage_ba4cddbf` (`global_message_id`),
  CONSTRAINT `be73d6672c3000f87521c37bc8ad4139` FOREIGN KEY (`global_message_id`) REFERENCES `status_globalstatusmessage` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `status_globalstatusmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status_globalstatusmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `message` longtext,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `status_globalstat_changed_by_id_76ab1cf17be5644d_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `status_globalstat_changed_by_id_76ab1cf17be5644d_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_anonymoususerid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_anonymoususerid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `anonymous_user_id` varchar(32) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `anonymous_user_id` (`anonymous_user_id`),
  KEY `student_anonymoususerid_user_id_1a18af72cf6b95f7_fk_auth_user_id` (`user_id`),
  KEY `student_anonymoususerid_ea134da7` (`course_id`),
  CONSTRAINT `student_anonymoususerid_user_id_1a18af72cf6b95f7_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseaccessrole`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseaccessrole` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `org` varchar(64) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `role` varchar(64) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_courseaccessrole_user_id_3203176c4f474414_uniq` (`user_id`,`org`,`course_id`,`role`),
  KEY `student_courseaccessrole_5a445d71` (`org`),
  KEY `student_courseaccessrole_ea134da7` (`course_id`),
  KEY `student_courseaccessrole_29a7e964` (`role`),
  CONSTRAINT `student_courseaccessrol_user_id_5e0f68b978ad0792_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseenrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseenrollment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `mode` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_courseenrollment_user_id_2d2a572f07dd8e37_uniq` (`user_id`,`course_id`),
  KEY `student_courseenrollment_ea134da7` (`course_id`),
  KEY `student_courseenrollment_e2fa5388` (`created`),
  CONSTRAINT `student_courseenrollmen_user_id_15beaaebc8333ce4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseenrollmentallowed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseenrollmentallowed` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `auto_enroll` tinyint(1) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_courseenrollmentallowed_email_6f3eafd4a6c58591_uniq` (`email`,`course_id`),
  KEY `student_courseenrollmentallowed_0c83f57c` (`email`),
  KEY `student_courseenrollmentallowed_ea134da7` (`course_id`),
  KEY `student_courseenrollmentallowed_e2fa5388` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_courseenrollmentattribute`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_courseenrollmentattribute` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `namespace` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `enrollment_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stu_enrollment_id_674188e6fcb084c_fk_student_courseenrollment_id` (`enrollment_id`),
  CONSTRAINT `stu_enrollment_id_674188e6fcb084c_fk_student_courseenrollment_id` FOREIGN KEY (`enrollment_id`) REFERENCES `student_courseenrollment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_dashboardconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_dashboardconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `recent_enrollment_time_delta` int(10) unsigned NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_dashboard_changed_by_id_4db1e1194c4ae32c_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `student_dashboard_changed_by_id_4db1e1194c4ae32c_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_enrollmentrefundconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_enrollmentrefundconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `refund_window_microseconds` bigint(20) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_enrollmen_changed_by_id_59c187ac05e64a11_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `student_enrollmen_changed_by_id_59c187ac05e64a11_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_entranceexamconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_entranceexamconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `updated` datetime(6) NOT NULL,
  `skip_entrance_exam` tinyint(1) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_entranceexamconfiguration_user_id_714c2ef6a88504f0_uniq` (`user_id`,`course_id`),
  KEY `student_entranceexamconfiguration_ea134da7` (`course_id`),
  KEY `student_entranceexamconfiguration_e2fa5388` (`created`),
  KEY `student_entranceexamconfiguration_0f81d52e` (`updated`),
  CONSTRAINT `student_entranceexamcon_user_id_530195af5babe0dd_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_historicalcourseenrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_historicalcourseenrollment` (
  `id` int(11) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `created` datetime(6) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `mode` varchar(100) NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`history_id`),
  KEY `student_histori_history_user_id_49fd2870709a6441_fk_auth_user_id` (`history_user_id`),
  KEY `student_historicalcourseenrollment_b80bb774` (`id`),
  KEY `student_historicalcourseenrollment_ea134da7` (`course_id`),
  KEY `student_historicalcourseenrollment_e2fa5388` (`created`),
  CONSTRAINT `student_histori_history_user_id_49fd2870709a6441_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_languageproficiency`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_languageproficiency` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(16) NOT NULL,
  `user_profile_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_languageproficiency_code_68e76171684c62e5_uniq` (`code`,`user_profile_id`),
  KEY `student_languageproficiency_06037614` (`user_profile_id`),
  CONSTRAINT `student__user_profile_id_283edb437b102619_fk_auth_userprofile_id` FOREIGN KEY (`user_profile_id`) REFERENCES `auth_userprofile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_linkedinaddtoprofileconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_linkedinaddtoprofileconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `company_identifier` longtext NOT NULL,
  `dashboard_tracking_code` longtext NOT NULL,
  `trk_partner_name` varchar(10) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_linkedina_changed_by_id_226a4de3af0f3296_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `student_linkedina_changed_by_id_226a4de3af0f3296_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_loginfailures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_loginfailures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `failure_count` int(11) NOT NULL,
  `lockout_until` datetime(6) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `student_loginfailures_user_id_3daac39f3118bac4_fk_auth_user_id` (`user_id`),
  CONSTRAINT `student_loginfailures_user_id_3daac39f3118bac4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_manualenrollmentaudit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_manualenrollmentaudit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enrolled_email` varchar(255) NOT NULL,
  `time_stamp` datetime(6) DEFAULT NULL,
  `state_transition` varchar(255) NOT NULL,
  `reason` longtext,
  `enrolled_by_id` int(11) DEFAULT NULL,
  `enrollment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_manualenr_enrolled_by_id_729cecdc9f746e2_fk_auth_user_id` (`enrolled_by_id`),
  KEY `st_enrollment_id_60349e74284df0d6_fk_student_courseenrollment_id` (`enrollment_id`),
  KEY `student_manualenrollmentaudit_ce9e7289` (`enrolled_email`),
  CONSTRAINT `st_enrollment_id_60349e74284df0d6_fk_student_courseenrollment_id` FOREIGN KEY (`enrollment_id`) REFERENCES `student_courseenrollment` (`id`),
  CONSTRAINT `student_manualenr_enrolled_by_id_729cecdc9f746e2_fk_auth_user_id` FOREIGN KEY (`enrolled_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_passwordhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_passwordhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `time_set` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `student_passwordhistory_user_id_21328c8c512d6c0d_fk_auth_user_id` (`user_id`),
  CONSTRAINT `student_passwordhistory_user_id_21328c8c512d6c0d_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_pendingemailchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_pendingemailchange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `new_email` varchar(255) NOT NULL,
  `activation_key` varchar(32) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `activation_key` (`activation_key`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `student_pendingemailchange_a4a65cd1` (`new_email`),
  CONSTRAINT `student_pendingemailcha_user_id_566caccc3f3c3966_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_pendingnamechange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_pendingnamechange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `new_name` varchar(255) NOT NULL,
  `rationale` varchar(1024) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `student_pendingnamechan_user_id_6c3c9d77fc5898a6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_usersignupsource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_usersignupsource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `site` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `student_usersignupsourc_user_id_4db69fdecf32119f_fk_auth_user_id` (`user_id`),
  KEY `student_usersignupsource_98defd6e` (`site`),
  CONSTRAINT `student_usersignupsourc_user_id_4db69fdecf32119f_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `student_userstanding`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_userstanding` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_status` varchar(31) NOT NULL,
  `standing_last_changed_at` datetime(6) NOT NULL,
  `changed_by_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `student_userstand_changed_by_id_23784b83f2849aff_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `student_userstand_changed_by_id_23784b83f2849aff_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `student_userstanding_user_id_6bb90abaaa05d42e_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
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
  KEY `student_usertestgroup_b068931c` (`name`)
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
  UNIQUE KEY `usertestgroup_id` (`usertestgroup_id`,`user_id`),
  KEY `student_usertestgroup_u_user_id_26c886de60cceacb_fk_auth_user_id` (`user_id`),
  CONSTRAINT `st_usertestgroup_id_3d634741f1dd4e4f_fk_student_usertestgroup_id` FOREIGN KEY (`usertestgroup_id`) REFERENCES `student_usertestgroup` (`id`),
  CONSTRAINT `student_usertestgroup_u_user_id_26c886de60cceacb_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `submissions_score`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions_score` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `points_earned` int(10) unsigned NOT NULL,
  `points_possible` int(10) unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reset` tinyint(1) NOT NULL,
  `student_item_id` int(11) NOT NULL,
  `submission_id` int(11),
  PRIMARY KEY (`id`),
  KEY `submissions_score_fde81f11` (`created_at`),
  KEY `submissions_score_02d5e83e` (`student_item_id`),
  KEY `submissions_score_1dd9cfcc` (`submission_id`),
  CONSTRAINT `s_student_item_id_7d4d4bb6a7dd0642_fk_submissions_studentitem_id` FOREIGN KEY (`student_item_id`) REFERENCES `submissions_studentitem` (`id`),
  CONSTRAINT `subm_submission_id_3fc975fe88442ff7_fk_submissions_submission_id` FOREIGN KEY (`submission_id`) REFERENCES `submissions_submission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `submissions_scoreannotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions_scoreannotation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `annotation_type` varchar(255) NOT NULL,
  `creator` varchar(255) NOT NULL,
  `reason` longtext NOT NULL,
  `score_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `submissions_sc_score_id_7b5ef248552cb857_fk_submissions_score_id` (`score_id`),
  KEY `submissions_scoreannotation_fd685234` (`annotation_type`),
  KEY `submissions_scoreannotation_ee243325` (`creator`),
  CONSTRAINT `submissions_sc_score_id_7b5ef248552cb857_fk_submissions_score_id` FOREIGN KEY (`score_id`) REFERENCES `submissions_score` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `submissions_scoresummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions_scoresummary` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `highest_id` int(11) NOT NULL,
  `latest_id` int(11) NOT NULL,
  `student_item_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_item_id` (`student_item_id`),
  KEY `submissions__highest_id_7fd91b8eb312c175_fk_submissions_score_id` (`highest_id`),
  KEY `submissions_s_latest_id_2b352506a35fd569_fk_submissions_score_id` (`latest_id`),
  CONSTRAINT `s_student_item_id_32fa0a425a149b1b_fk_submissions_studentitem_id` FOREIGN KEY (`student_item_id`) REFERENCES `submissions_studentitem` (`id`),
  CONSTRAINT `submissions__highest_id_7fd91b8eb312c175_fk_submissions_score_id` FOREIGN KEY (`highest_id`) REFERENCES `submissions_score` (`id`),
  CONSTRAINT `submissions_s_latest_id_2b352506a35fd569_fk_submissions_score_id` FOREIGN KEY (`latest_id`) REFERENCES `submissions_score` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `submissions_studentitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions_studentitem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `item_id` varchar(255) NOT NULL,
  `item_type` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submissions_studentitem_course_id_6a6eccbdec6ffd0b_uniq` (`course_id`,`student_id`,`item_id`),
  KEY `submissions_studentitem_30a811f6` (`student_id`),
  KEY `submissions_studentitem_ea134da7` (`course_id`),
  KEY `submissions_studentitem_82bfda79` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `submissions_submission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions_submission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `attempt_number` int(10) unsigned NOT NULL,
  `submitted_at` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `raw_answer` longtext NOT NULL,
  `student_item_id` int(11) NOT NULL,
  `status` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `su_student_item_id_d3801ff833d05b1_fk_submissions_studentitem_id` (`student_item_id`),
  KEY `submissions_submission_ef7c876f` (`uuid`),
  KEY `submissions_submission_22bb6ff9` (`submitted_at`),
  KEY `submissions_submission_fde81f11` (`created_at`),
  CONSTRAINT `su_student_item_id_d3801ff833d05b1_fk_submissions_studentitem_id` FOREIGN KEY (`student_item_id`) REFERENCES `submissions_studentitem` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `survey_surveyanswer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `survey_surveyanswer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `field_name` varchar(255) NOT NULL,
  `field_value` varchar(1024) NOT NULL,
  `course_key` varchar(255) DEFAULT NULL,
  `form_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `survey_surveyanswer_73f329f1` (`field_name`),
  KEY `survey_surveyanswer_c8235886` (`course_key`),
  KEY `survey_surveyanswer_d6cba1ad` (`form_id`),
  KEY `survey_surveyanswer_e8701ad4` (`user_id`),
  CONSTRAINT `survey_surveyan_form_id_1c835afe12a54912_fk_survey_surveyform_id` FOREIGN KEY (`form_id`) REFERENCES `survey_surveyform` (`id`),
  CONSTRAINT `survey_surveyanswer_user_id_4e77d83a82fd0b2b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `survey_surveyform`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `survey_surveyform` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `name` varchar(255) NOT NULL,
  `form` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tagging_tagavailablevalues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tagging_tagavailablevalues` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value` varchar(255) NOT NULL,
  `category_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tagging_tagavailablevalues_b583a629` (`category_id`),
  CONSTRAINT `tagging_category_id_40780d45c76e4f97_fk_tagging_tagcategories_id` FOREIGN KEY (`category_id`) REFERENCES `tagging_tagcategories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tagging_tagcategories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tagging_tagcategories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `teams_courseteam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `teams_courseteam` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `team_id` varchar(255) NOT NULL,
  `discussion_topic_id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `topic_id` varchar(255) NOT NULL,
  `date_created` datetime(6) NOT NULL,
  `description` varchar(300) NOT NULL,
  `country` varchar(2) NOT NULL,
  `language` varchar(16) NOT NULL,
  `last_activity_at` datetime(6) NOT NULL,
  `team_size` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `team_id` (`team_id`),
  UNIQUE KEY `discussion_topic_id` (`discussion_topic_id`),
  KEY `teams_courseteam_b068931c` (`name`),
  KEY `teams_courseteam_ea134da7` (`course_id`),
  KEY `teams_courseteam_19b4d727` (`topic_id`),
  KEY `teams_courseteam_5ea53fcc` (`last_activity_at`),
  KEY `teams_courseteam_181d83a1` (`team_size`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `teams_courseteammembership`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `teams_courseteammembership` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_joined` datetime(6) NOT NULL,
  `last_activity_at` datetime(6) NOT NULL,
  `team_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `teams_courseteammembership_user_id_48efa8e8971947c3_uniq` (`user_id`,`team_id`),
  KEY `teams_courseteam_team_id_594700d19b04f922_fk_teams_courseteam_id` (`team_id`),
  CONSTRAINT `teams_courseteam_team_id_594700d19b04f922_fk_teams_courseteam_id` FOREIGN KEY (`team_id`) REFERENCES `teams_courseteam` (`id`),
  CONSTRAINT `teams_courseteammembers_user_id_2d93b28be22c3c40_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_ltiproviderconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_ltiproviderconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `icon_class` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `secondary` tinyint(1) NOT NULL,
  `skip_registration_form` tinyint(1) NOT NULL,
  `skip_email_verification` tinyint(1) NOT NULL,
  `lti_consumer_key` varchar(255) NOT NULL,
  `lti_hostname` varchar(255) NOT NULL,
  `lti_consumer_secret` varchar(255) NOT NULL,
  `lti_max_timestamp_age` int(11) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `icon_image` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth__changed_by_id_7749e09fd5f71ab0_fk_auth_user_id` (`changed_by_id`),
  KEY `third_party_auth_ltiproviderconfig_fe8da584` (`lti_hostname`),
  CONSTRAINT `third_party_auth__changed_by_id_7749e09fd5f71ab0_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_oauth2providerconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_oauth2providerconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `icon_class` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `secondary` tinyint(1) NOT NULL,
  `skip_registration_form` tinyint(1) NOT NULL,
  `skip_email_verification` tinyint(1) NOT NULL,
  `backend_name` varchar(50) NOT NULL,
  `key` longtext NOT NULL,
  `secret` longtext NOT NULL,
  `other_settings` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `icon_image` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth__changed_by_id_17044d1cd96e8d57_fk_auth_user_id` (`changed_by_id`),
  KEY `third_party_auth_oauth2providerconfig_abcd61c0` (`backend_name`),
  CONSTRAINT `third_party_auth__changed_by_id_17044d1cd96e8d57_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_providerapipermissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_providerapipermissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` varchar(255) NOT NULL,
  `client_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth__client_id_648d3f6d6109693b_fk_oauth2_client_id` (`client_id`),
  CONSTRAINT `third_party_auth__client_id_648d3f6d6109693b_fk_oauth2_client_id` FOREIGN KEY (`client_id`) REFERENCES `oauth2_client` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `private_key` longtext NOT NULL,
  `public_key` longtext NOT NULL,
  `entity_id` varchar(255) NOT NULL,
  `org_info_str` longtext NOT NULL,
  `other_config_str` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth__changed_by_id_67a92ed1a69a5d1f_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `third_party_auth__changed_by_id_67a92ed1a69a5d1f_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlproviderconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlproviderconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `icon_class` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `secondary` tinyint(1) NOT NULL,
  `skip_registration_form` tinyint(1) NOT NULL,
  `skip_email_verification` tinyint(1) NOT NULL,
  `backend_name` varchar(50) NOT NULL,
  `idp_slug` varchar(30) NOT NULL,
  `entity_id` varchar(255) NOT NULL,
  `metadata_source` varchar(255) NOT NULL,
  `attr_user_permanent_id` varchar(128) NOT NULL,
  `attr_full_name` varchar(128) NOT NULL,
  `attr_first_name` varchar(128) NOT NULL,
  `attr_last_name` varchar(128) NOT NULL,
  `attr_username` varchar(128) NOT NULL,
  `attr_email` varchar(128) NOT NULL,
  `other_settings` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `icon_image` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth__changed_by_id_508190ecd0b0e845_fk_auth_user_id` (`changed_by_id`),
  KEY `third_party_auth_samlproviderconfig_098674f1` (`idp_slug`),
  CONSTRAINT `third_party_auth__changed_by_id_508190ecd0b0e845_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlproviderdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlproviderdata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fetched_at` datetime(6) NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `entity_id` varchar(255) NOT NULL,
  `sso_url` varchar(200) NOT NULL,
  `public_key` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth_samlproviderdata_d674fcb7` (`fetched_at`),
  KEY `third_party_auth_samlproviderdata_81aefa79` (`expires_at`),
  KEY `third_party_auth_samlproviderdata_dffc4713` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `thumbnail_kvstore`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `thumbnail_kvstore` (
  `key` varchar(200) NOT NULL,
  `value` longtext NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_oauth2providerconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_oauth2providerconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `icon_class` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `backend_name` varchar(50) NOT NULL,
  `key` longtext NOT NULL,
  `secret` longtext NOT NULL,
  `other_settings` longtext NOT NULL,
  `secondary` tinyint(1) NOT NULL,
  `skip_registration_form` tinyint(1) NOT NULL,
  `skip_email_verification` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth_oauth2providerconfig_16905482` (`changed_by_id`),
  KEY `third_party_auth_oauth2providerconfig_83e7b51d` (`backend_name`),
  CONSTRAINT `changed_by_id_refs_id_cd05125b` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `private_key` longtext NOT NULL,
  `public_key` longtext NOT NULL,
  `entity_id` varchar(255) NOT NULL,
  `org_info_str` longtext NOT NULL,
  `other_config_str` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth_samlconfiguration_16905482` (`changed_by_id`),
  CONSTRAINT `changed_by_id_refs_id_7817e9cd` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlproviderconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlproviderconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `icon_class` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `backend_name` varchar(50) NOT NULL,
  `idp_slug` varchar(30) NOT NULL,
  `entity_id` varchar(255) NOT NULL,
  `metadata_source` varchar(255) NOT NULL,
  `attr_user_permanent_id` varchar(128) NOT NULL,
  `attr_full_name` varchar(128) NOT NULL,
  `attr_first_name` varchar(128) NOT NULL,
  `attr_last_name` varchar(128) NOT NULL,
  `attr_username` varchar(128) NOT NULL,
  `attr_email` varchar(128) NOT NULL,
  `other_settings` longtext NOT NULL,
  `secondary` tinyint(1) NOT NULL,
  `skip_registration_form` tinyint(1) NOT NULL,
  `skip_email_verification` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth_samlproviderconfig_16905482` (`changed_by_id`),
  KEY `third_party_auth_samlproviderconfig_5112c6f2` (`idp_slug`),
  CONSTRAINT `changed_by_id_refs_id_63b11ff7` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `third_party_auth_samlproviderdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `third_party_auth_samlproviderdata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fetched_at` datetime NOT NULL,
  `expires_at` datetime DEFAULT NULL,
  `entity_id` varchar(255) NOT NULL,
  `sso_url` varchar(200) NOT NULL,
  `public_key` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `third_party_auth_samlproviderdata_744ae5b8` (`fetched_at`),
  KEY `third_party_auth_samlproviderdata_8e1ddc1d` (`expires_at`),
  KEY `third_party_auth_samlproviderdata_2ce815e9` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `track_trackinglog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `track_trackinglog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtcreated` datetime(6) NOT NULL,
  `username` varchar(32) NOT NULL,
  `ip` varchar(32) NOT NULL,
  `event_source` varchar(32) NOT NULL,
  `event_type` varchar(512) NOT NULL,
  `event` longtext NOT NULL,
  `agent` varchar(256) NOT NULL,
  `page` varchar(512) DEFAULT NULL,
  `time` datetime(6) NOT NULL,
  `host` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `user_api_usercoursetag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_api_usercoursetag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(255) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_api_usercoursetag_user_id_64d9a32c9890f610_uniq` (`user_id`,`course_id`,`key`),
  KEY `user_api_usercoursetag_3c6e0b8a` (`key`),
  KEY `user_api_usercoursetag_ea134da7` (`course_id`),
  CONSTRAINT `user_api_usercoursetag_user_id_2692245bbb861fc2_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `user_api_userorgtag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_api_userorgtag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `key` varchar(255) NOT NULL,
  `org` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_api_userorgtag_user_id_694f9e3322120c6f_uniq` (`user_id`,`org`,`key`),
  KEY `user_api_userorgtag_3c6e0b8a` (`key`),
  KEY `user_api_userorgtag_5a445d71` (`org`),
  CONSTRAINT `user_api_userorgtag_user_id_16c7189496b4df00_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `user_api_userpreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_api_userpreference` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_api_userpreference_user_id_4e4942d73f760072_uniq` (`user_id`,`key`),
  KEY `user_api_userpreference_3c6e0b8a` (`key`),
  CONSTRAINT `user_api_userpreference_user_id_41f12e3954b69095_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `util_ratelimitconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `util_ratelimitconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `util_ratelimitcon_changed_by_id_2c8891cb4854f3b5_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `util_ratelimitcon_changed_by_id_2c8891cb4854f3b5_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verified_track_content_verifiedtrackcohortedcourse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verified_track_content_verifiedtrackcohortedcourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_key` varchar(255) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `verified_cohort_name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_key` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_historicalverificationdeadline`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_historicalverificationdeadline` (
  `id` int(11) NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `deadline` datetime(6) NOT NULL,
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `history_date` datetime(6) NOT NULL,
  `history_type` varchar(1) NOT NULL,
  `history_user_id` int(11) DEFAULT NULL,
  `deadline_is_explicit` tinyint(1) NOT NULL,
  PRIMARY KEY (`history_id`),
  KEY `verify_student__history_user_id_1e374d24cb7902c2_fk_auth_user_id` (`history_user_id`),
  KEY `verify_student_historicalverificationdeadline_b80bb774` (`id`),
  KEY `verify_student_historicalverificationdeadline_c8235886` (`course_key`),
  CONSTRAINT `verify_student__history_user_id_1e374d24cb7902c2_fk_auth_user_id` FOREIGN KEY (`history_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_icrvstatusemailsconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_icrvstatusemailsconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `verify_student_icr_changed_by_id_52e319582f18ea3_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `verify_student_icr_changed_by_id_52e319582f18ea3_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_incoursereverificationconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_incoursereverificationconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `verify_student_in_changed_by_id_1f3e3fa462a6ded6_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `verify_student_in_changed_by_id_1f3e3fa462a6ded6_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_skippedreverification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_skippedreverification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `checkpoint_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `verify_student_skippedreverificati_user_id_1e8af5a5e735aa1a_uniq` (`user_id`,`course_id`),
  KEY `verify_student_skippedreverification_ea134da7` (`course_id`),
  KEY `verify_student_skippedreverification_bef2d98a` (`checkpoint_id`),
  KEY `verify_student_skippedreverification_e8701ad4` (`user_id`),
  CONSTRAINT `D759ffa5ca66ef1a2c8c200f7a21365b` FOREIGN KEY (`checkpoint_id`) REFERENCES `verify_student_verificationcheckpoint` (`id`),
  CONSTRAINT `verify_student_skippedr_user_id_6752b392e3d3c501_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_softwaresecurephotoverification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_softwaresecurephotoverification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status` varchar(100) NOT NULL,
  `status_changed` datetime(6) NOT NULL,
  `name` varchar(255) NOT NULL,
  `face_image_url` varchar(255) NOT NULL,
  `photo_id_image_url` varchar(255) NOT NULL,
  `receipt_id` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `display` tinyint(1) NOT NULL,
  `submitted_at` datetime(6) DEFAULT NULL,
  `reviewing_service` varchar(255) NOT NULL,
  `error_msg` longtext NOT NULL,
  `error_code` varchar(50) NOT NULL,
  `photo_id_key` longtext NOT NULL,
  `copy_id_photo_from_id` int(11) DEFAULT NULL,
  `reviewing_user_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D01dce17b91c9382bd80d4be23a3e0cf` (`copy_id_photo_from_id`),
  KEY `verify_studen_reviewing_user_id_727fae1d0bcf8aaf_fk_auth_user_id` (`reviewing_user_id`),
  KEY `verify_student_software_user_id_61ffab9c12020106_fk_auth_user_id` (`user_id`),
  KEY `verify_student_softwaresecurephotoverification_f6fc3014` (`receipt_id`),
  KEY `verify_student_softwaresecurephotoverification_fde81f11` (`created_at`),
  KEY `verify_student_softwaresecurephotoverification_afd1a1a8` (`updated_at`),
  KEY `verify_student_softwaresecurephotoverification_ebf78b51` (`display`),
  KEY `verify_student_softwaresecurephotoverification_22bb6ff9` (`submitted_at`),
  CONSTRAINT `D01dce17b91c9382bd80d4be23a3e0cf` FOREIGN KEY (`copy_id_photo_from_id`) REFERENCES `verify_student_softwaresecurephotoverification` (`id`),
  CONSTRAINT `verify_studen_reviewing_user_id_727fae1d0bcf8aaf_fk_auth_user_id` FOREIGN KEY (`reviewing_user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `verify_student_software_user_id_61ffab9c12020106_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_verificationcheckpoint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_verificationcheckpoint` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` varchar(255) NOT NULL,
  `checkpoint_location` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `verify_student_verificationcheck_course_id_2c6a1f5c22b4cc19_uniq` (`course_id`,`checkpoint_location`),
  KEY `verify_student_verificationcheckpoint_ea134da7` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_verificationcheckpoint_photo_verification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_verificationcheckpoint_photo_verification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `verificationcheckpoint_id` int(11) NOT NULL,
  `softwaresecurephotoverification_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `verificationcheckpoint_id` (`verificationcheckpoint_id`,`softwaresecurephotoverification_id`),
  KEY `c7846aea49a044a1161a4b9b6d70e050` (`softwaresecurephotoverification_id`),
  CONSTRAINT `c7846aea49a044a1161a4b9b6d70e050` FOREIGN KEY (`softwaresecurephotoverification_id`) REFERENCES `verify_student_softwaresecurephotoverification` (`id`),
  CONSTRAINT `e4d180f9ca43c3b66693c416a36cfb9d` FOREIGN KEY (`verificationcheckpoint_id`) REFERENCES `verify_student_verificationcheckpoint` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_verificationdeadline`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_verificationdeadline` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `course_key` varchar(255) NOT NULL,
  `deadline` datetime(6) NOT NULL,
  `deadline_is_explicit` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_key` (`course_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `verify_student_verificationstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verify_student_verificationstatus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status` varchar(32) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `response` longtext,
  `error` longtext,
  `checkpoint_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `D4cefb6d3d71c9b26af2a5ece4c37277` (`checkpoint_id`),
  KEY `verify_student_verifica_user_id_5c19fcd6dc05f211_fk_auth_user_id` (`user_id`),
  KEY `verify_student_verificationstatus_9acb4454` (`status`),
  CONSTRAINT `D4cefb6d3d71c9b26af2a5ece4c37277` FOREIGN KEY (`checkpoint_id`) REFERENCES `verify_student_verificationcheckpoint` (`id`),
  CONSTRAINT `verify_student_verifica_user_id_5c19fcd6dc05f211_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_article` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `group_read` tinyint(1) NOT NULL,
  `group_write` tinyint(1) NOT NULL,
  `other_read` tinyint(1) NOT NULL,
  `other_write` tinyint(1) NOT NULL,
  `current_revision_id` int(11),
  `group_id` int(11),
  `owner_id` int(11),
  PRIMARY KEY (`id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  KEY `wiki_article_0e939a4f` (`group_id`),
  KEY `wiki_article_5e7b1936` (`owner_id`),
  CONSTRAINT `current_revision_id_42a9dbec1e0dd15c_fk_wiki_articlerevision_id` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `wiki_article_group_id_2b38601b6aa39f3d_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `wiki_article_owner_id_b1c1e44609a378f_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articleforobject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articleforobject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `object_id` int(10) unsigned NOT NULL,
  `is_mptt` tinyint(1) NOT NULL,
  `article_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_articleforobject_content_type_id_27c4cce189b3bcab_uniq` (`content_type_id`,`object_id`),
  KEY `wiki_articleforobj_article_id_6effcfadf020e71_fk_wiki_article_id` (`article_id`),
  CONSTRAINT `wiki__content_type_id_6a39c68b7a20c3c4_fk_django_content_type_id` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `wiki_articleforobj_article_id_6effcfadf020e71_fk_wiki_article_id` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_articleplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_articleplugin` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deleted` tinyint(1) NOT NULL,
  `created` datetime(6) NOT NULL,
  `article_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_articleplugin_a00c1b00` (`article_id`),
  CONSTRAINT `wiki_articleplugi_article_id_2d2c794af030d9dd_fk_wiki_article_id` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`)
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
  `modified` datetime(6) NOT NULL,
  `created` datetime(6) NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `content` longtext NOT NULL,
  `title` varchar(512) NOT NULL,
  `article_id` int(11) NOT NULL,
  `previous_revision_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_articlerevision_article_id_4b4e7910c8e7b2d0_uniq` (`article_id`,`revision_number`),
  KEY `fae2b1c6e892c699844d5dda69aeb89e` (`previous_revision_id`),
  KEY `wiki_articlerevision_user_id_183520686b6ead55_fk_auth_user_id` (`user_id`),
  CONSTRAINT `fae2b1c6e892c699844d5dda69aeb89e` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `wiki_articlerevis_article_id_1f2c587981af1463_fk_wiki_article_id` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`),
  CONSTRAINT `wiki_articlerevision_user_id_183520686b6ead55_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_attachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_attachment` (
  `reusableplugin_ptr_id` int(11) NOT NULL,
  `original_filename` varchar(256) DEFAULT NULL,
  `current_revision_id` int(11),
  PRIMARY KEY (`reusableplugin_ptr_id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  CONSTRAINT `D32d32ecb0471dc863a4e19562842024` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_attachmentrevision` (`id`),
  CONSTRAINT `D7d9a9637c738daa9daff735f9023fbe` FOREIGN KEY (`reusableplugin_ptr_id`) REFERENCES `wiki_reusableplugin` (`articleplugin_ptr_id`)
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
  `modified` datetime(6) NOT NULL,
  `created` datetime(6) NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `file` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `attachment_id` int(11) NOT NULL,
  `previous_revision_id` int(11),
  `user_id` int(11),
  PRIMARY KEY (`id`),
  KEY `wiki_attachmentrevision_07ba63f5` (`attachment_id`),
  KEY `wiki_attachmentrevision_e8680b8a` (`previous_revision_id`),
  KEY `wiki_attachmentrevision_e8701ad4` (`user_id`),
  CONSTRAINT `D68d5cd540b66f536228137e518081f8` FOREIGN KEY (`attachment_id`) REFERENCES `wiki_attachment` (`reusableplugin_ptr_id`),
  CONSTRAINT `D8c1f0a8f0ddceb9c3ebc94379fe22c9` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_attachmentrevision` (`id`),
  CONSTRAINT `wiki_attachmentrevision_user_id_427e3f452b4bfdcd_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_image` (
  `revisionplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`revisionplugin_ptr_id`),
  CONSTRAINT `D243c0b311b744e834d2b1ee4d22fc5f` FOREIGN KEY (`revisionplugin_ptr_id`) REFERENCES `wiki_revisionplugin` (`articleplugin_ptr_id`)
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
  CONSTRAINT `fcc7a25da8b3b9e0494c126ccf17852e` FOREIGN KEY (`revisionpluginrevision_ptr_id`) REFERENCES `wiki_revisionpluginrevision` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_reusableplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_reusableplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  CONSTRAINT `w_articleplugin_ptr_id_657a603b3f46a3e3_fk_wiki_articleplugin_id` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
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
  UNIQUE KEY `reusableplugin_id` (`reusableplugin_id`,`article_id`),
  KEY `wiki_reusableplug_article_id_5e893d3b3fb4f7fa_fk_wiki_article_id` (`article_id`),
  CONSTRAINT `a9f9f50fd4e8fdafe7ffc0c1a145fee3` FOREIGN KEY (`reusableplugin_id`) REFERENCES `wiki_reusableplugin` (`articleplugin_ptr_id`),
  CONSTRAINT `wiki_reusableplug_article_id_5e893d3b3fb4f7fa_fk_wiki_article_id` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_revisionplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_revisionplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  `current_revision_id` int(11),
  PRIMARY KEY (`articleplugin_ptr_id`),
  UNIQUE KEY `current_revision_id` (`current_revision_id`),
  CONSTRAINT `D03d76148e98b4bc99e3137189894366` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revisionpluginrevision` (`id`),
  CONSTRAINT `w_articleplugin_ptr_id_35fa87d70e9722a1_fk_wiki_articleplugin_id` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
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
  `modified` datetime(6) NOT NULL,
  `created` datetime(6) NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `plugin_id` int(11) NOT NULL,
  `previous_revision_id` int(11),
  `user_id` int(11),
  PRIMARY KEY (`id`),
  KEY `wiki_revisionpluginrevision_b25eaab4` (`plugin_id`),
  KEY `wiki_revisionpluginrevision_e8680b8a` (`previous_revision_id`),
  KEY `wiki_revisionpluginrevision_e8701ad4` (`user_id`),
  CONSTRAINT `D9574e2f57b828a85a24838761473871` FOREIGN KEY (`plugin_id`) REFERENCES `wiki_revisionplugin` (`articleplugin_ptr_id`),
  CONSTRAINT `e524c4f887e857f93c39356f7cf7d4df` FOREIGN KEY (`previous_revision_id`) REFERENCES `wiki_revisionpluginrevision` (`id`),
  CONSTRAINT `wiki_revisionpluginrevi_user_id_55a00bd0e2532762_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_simpleplugin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_simpleplugin` (
  `articleplugin_ptr_id` int(11) NOT NULL,
  `article_revision_id` int(11) NOT NULL,
  PRIMARY KEY (`articleplugin_ptr_id`),
  KEY `w_article_revision_id_8be41c856aa0285_fk_wiki_articlerevision_id` (`article_revision_id`),
  CONSTRAINT `w_article_revision_id_8be41c856aa0285_fk_wiki_articlerevision_id` FOREIGN KEY (`article_revision_id`) REFERENCES `wiki_articlerevision` (`id`),
  CONSTRAINT `w_articleplugin_ptr_id_36e661324cc27ff2_fk_wiki_articleplugin_id` FOREIGN KEY (`articleplugin_ptr_id`) REFERENCES `wiki_articleplugin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `wiki_urlpath`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_urlpath` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `slug` varchar(50) DEFAULT NULL,
  `lft` int(10) unsigned NOT NULL,
  `rght` int(10) unsigned NOT NULL,
  `tree_id` int(10) unsigned NOT NULL,
  `level` int(10) unsigned NOT NULL,
  `article_id` int(11) NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wiki_urlpath_site_id_124f6aa7b2cc9b82_uniq` (`site_id`,`parent_id`,`slug`),
  KEY `wiki_urlpath_article_id_1d1c5eb9a64e1390_fk_wiki_article_id` (`article_id`),
  KEY `wiki_urlpath_2dbcba41` (`slug`),
  KEY `wiki_urlpath_caf7cc51` (`lft`),
  KEY `wiki_urlpath_3cfbd988` (`rght`),
  KEY `wiki_urlpath_656442a0` (`tree_id`),
  KEY `wiki_urlpath_c9e9a848` (`level`),
  KEY `wiki_urlpath_6be37982` (`parent_id`),
  CONSTRAINT `wiki_urlpath_article_id_1d1c5eb9a64e1390_fk_wiki_article_id` FOREIGN KEY (`article_id`) REFERENCES `wiki_article` (`id`),
  CONSTRAINT `wiki_urlpath_parent_id_24eab80cd168595f_fk_wiki_urlpath_id` FOREIGN KEY (`parent_id`) REFERENCES `wiki_urlpath` (`id`),
  CONSTRAINT `wiki_urlpath_site_id_4f30e731b0464e80_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `workflow_assessmentworkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workflow_assessmentworkflow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `status` varchar(100) NOT NULL,
  `status_changed` datetime(6) NOT NULL,
  `submission_uuid` varchar(36) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `course_id` varchar(255) NOT NULL,
  `item_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_uuid` (`submission_uuid`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `workflow_assessmentworkflow_ea134da7` (`course_id`),
  KEY `workflow_assessmentworkflow_82bfda79` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `workflow_assessmentworkflowcancellation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workflow_assessmentworkflowcancellation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `comments` longtext NOT NULL,
  `cancelled_by_id` varchar(40) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `workflow_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `w_workflow_id_581d7b320743ff70_fk_workflow_assessmentworkflow_id` (`workflow_id`),
  KEY `workflow_assessmentworkflowcancellation_195d4285` (`cancelled_by_id`),
  KEY `workflow_assessmentworkflowcancellation_fde81f11` (`created_at`),
  CONSTRAINT `w_workflow_id_581d7b320743ff70_fk_workflow_assessmentworkflow_id` FOREIGN KEY (`workflow_id`) REFERENCES `workflow_assessmentworkflow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `workflow_assessmentworkflowstep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workflow_assessmentworkflowstep` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `submitter_completed_at` datetime(6) DEFAULT NULL,
  `assessment_completed_at` datetime(6) DEFAULT NULL,
  `order_num` int(10) unsigned NOT NULL,
  `workflow_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `w_workflow_id_4939c36cf6220ba3_fk_workflow_assessmentworkflow_id` (`workflow_id`),
  CONSTRAINT `w_workflow_id_4939c36cf6220ba3_fk_workflow_assessmentworkflow_id` FOREIGN KEY (`workflow_id`) REFERENCES `workflow_assessmentworkflow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `xblock_config_studioconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xblock_config_studioconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `disabled_blocks` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `xblock_config_stu_changed_by_id_58f0a899052499fd_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `xblock_config_stu_changed_by_id_58f0a899052499fd_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `xblock_django_xblockdisableconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xblock_django_xblockdisableconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `disabled_blocks` longtext NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `disabled_create_blocks` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `xblock_django_xbl_changed_by_id_429bdccb9201831c_fk_auth_user_id` (`changed_by_id`),
  CONSTRAINT `xblock_django_xbl_changed_by_id_429bdccb9201831c_fk_auth_user_id` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `xblock_django_xblockdisableconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xblock_django_xblockdisableconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `change_date` datetime NOT NULL,
  `changed_by_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `disabled_blocks` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `xblock_django_xblockdisableconfig_16905482` (`changed_by_id`),
  CONSTRAINT `changed_by_id_refs_id_1ff69d70` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`)
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

