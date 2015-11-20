-- MySQL dump 10.13  Distrib 5.6.24, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: edxtest
-- ------------------------------------------------------
-- Server version	5.6.24-2+deb.sury.org~precise+2

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

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2015-11-20 03:58:09.368524'),(2,'auth','0001_initial','2015-11-20 03:58:09.659738'),(3,'admin','0001_initial','2015-11-20 03:58:09.746550'),(4,'assessment','0001_initial','2015-11-20 03:58:13.071977'),(5,'contenttypes','0002_remove_content_type_name','2015-11-20 03:58:13.229291'),(6,'auth','0002_alter_permission_name_max_length','2015-11-20 03:58:13.285517'),(7,'auth','0003_alter_user_email_max_length','2015-11-20 03:58:13.335628'),(8,'auth','0004_alter_user_username_opts','2015-11-20 03:58:13.365042'),(9,'auth','0005_alter_user_last_login_null','2015-11-20 03:58:13.431692'),(10,'auth','0006_require_contenttypes_0002','2015-11-20 03:58:13.438038'),(11,'certificates','0001_initial','2015-11-20 03:58:14.292352'),(12,'certificates','0002_data__certificatehtmlviewconfiguration_data','2015-11-20 03:58:14.312191'),(13,'certificates','0003_data__default_modes','2015-11-20 03:58:14.386829'),(14,'badges','0001_initial','2015-11-20 03:58:14.727409'),(15,'badges','0002_data__migrate_assertions','2015-11-20 03:58:14.775762'),(16,'branding','0001_initial','2015-11-20 03:58:14.940215'),(17,'bulk_email','0001_initial','2015-11-20 03:58:15.337493'),(18,'bulk_email','0002_data__load_course_email_template','2015-11-20 03:58:15.401633'),(19,'certificates','0004_schema__remove_badges','2015-11-20 03:58:15.606317'),(20,'commerce','0001_data__add_ecommerce_service_user','2015-11-20 03:58:15.634087'),(21,'cors_csrf','0001_initial','2015-11-20 03:58:15.731634'),(22,'course_action_state','0001_initial','2015-11-20 03:58:16.019106'),(23,'course_groups','0001_initial','2015-11-20 03:58:17.057577'),(24,'course_modes','0001_initial','2015-11-20 03:58:17.201537'),(25,'course_overviews','0001_initial','2015-11-20 03:58:17.298037'),(26,'course_structures','0001_initial','2015-11-20 03:58:17.337568'),(27,'courseware','0001_initial','2015-11-20 03:58:19.359709'),(28,'credit','0001_initial','2015-11-20 03:58:21.398987'),(29,'dark_lang','0001_initial','2015-11-20 03:58:21.556640'),(30,'dark_lang','0002_data__enable_on_install','2015-11-20 03:58:21.585328'),(31,'default','0001_initial','2015-11-20 03:58:22.089053'),(32,'default','0002_add_related_name','2015-11-20 03:58:22.254370'),(33,'default','0003_alter_email_max_length','2015-11-20 03:58:22.328842'),(34,'django_comment_common','0001_initial','2015-11-20 03:58:22.790885'),(35,'django_notify','0001_initial','2015-11-20 03:58:23.645875'),(36,'django_openid_auth','0001_initial','2015-11-20 03:58:23.959222'),(37,'edx_proctoring','0001_initial','2015-11-20 03:58:27.615700'),(38,'edxval','0001_initial','2015-11-20 03:58:29.003257'),(39,'edxval','0002_data__default_profiles','2015-11-20 03:58:29.044698'),(40,'embargo','0001_initial','2015-11-20 03:58:29.992344'),(41,'embargo','0002_data__add_countries','2015-11-20 03:58:30.502644'),(42,'external_auth','0001_initial','2015-11-20 03:58:31.124291'),(43,'foldit','0001_initial','2015-11-20 03:58:32.069377'),(44,'instructor_task','0001_initial','2015-11-20 03:58:32.452785'),(45,'licenses','0001_initial','2015-11-20 03:58:32.807565'),(46,'lms_xblock','0001_initial','2015-11-20 03:58:33.111775'),(47,'milestones','0001_initial','2015-11-20 03:58:34.203476'),(48,'milestones','0002_data__seed_relationship_types','2015-11-20 03:58:34.241704'),(49,'mobile_api','0001_initial','2015-11-20 03:58:34.558943'),(50,'notes','0001_initial','2015-11-20 03:58:34.970037'),(51,'oauth2','0001_initial','2015-11-20 03:58:37.693187'),(52,'oauth2_provider','0001_initial','2015-11-20 03:58:38.010637'),(53,'oauth_provider','0001_initial','2015-11-20 03:58:38.888032'),(54,'organizations','0001_initial','2015-11-20 03:58:39.133025'),(55,'organizations','0002_auto_20151119_2048','2015-11-20 03:58:39.178554'),(56,'programs','0001_initial','2015-11-20 03:58:39.552352'),(57,'programs','0002_programsapiconfig_cache_ttl','2015-11-20 03:58:39.945670'),(58,'psychometrics','0001_initial','2015-11-20 03:58:40.408258'),(59,'self_paced','0001_initial','2015-11-20 03:58:40.887405'),(60,'sessions','0001_initial','2015-11-20 03:58:40.961522'),(61,'student','0001_initial','2015-11-20 03:58:53.330542'),(62,'shoppingcart','0001_initial','2015-11-20 03:59:06.105155'),(63,'sites','0001_initial','2015-11-20 03:59:06.170737'),(64,'splash','0001_initial','2015-11-20 03:59:06.979616'),(65,'status','0001_initial','2015-11-20 03:59:08.403415'),(66,'submissions','0001_initial','2015-11-20 03:59:09.307549'),(67,'survey','0001_initial','2015-11-20 03:59:11.005609'),(68,'teams','0001_initial','2015-11-20 03:59:12.867020'),(69,'third_party_auth','0001_initial','2015-11-20 03:59:16.173372'),(70,'track','0001_initial','2015-11-20 03:59:16.246684'),(71,'user_api','0001_initial','2015-11-20 03:59:21.308311'),(72,'util','0001_initial','2015-11-20 03:59:21.958312'),(73,'util','0002_data__default_rate_limit_config','2015-11-20 03:59:22.022093'),(74,'verify_student','0001_initial','2015-11-20 03:59:31.063750'),(75,'wiki','0001_initial','2015-11-20 03:59:55.197507'),(76,'workflow','0001_initial','2015-11-20 03:59:55.550654'),(77,'xblock_django','0001_initial','2015-11-20 03:59:56.349274');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-11-20  4:00:07
