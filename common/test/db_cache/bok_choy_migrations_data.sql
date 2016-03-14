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
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2015-11-18 15:37:03.679215'),(2,'auth','0001_initial','2015-11-18 15:37:04.239453'),(3,'admin','0001_initial','2015-11-18 15:37:04.375156'),(4,'assessment','0001_initial','2015-11-18 15:37:09.037208'),(5,'contenttypes','0002_remove_content_type_name','2015-11-18 15:37:09.345424'),(6,'auth','0002_alter_permission_name_max_length','2015-11-18 15:37:09.479742'),(7,'auth','0003_alter_user_email_max_length','2015-11-18 15:37:09.677049'),(8,'auth','0004_alter_user_username_opts','2015-11-18 15:37:09.805606'),(9,'auth','0005_alter_user_last_login_null','2015-11-18 15:37:09.949394'),(10,'auth','0006_require_contenttypes_0002','2015-11-18 15:37:09.978283'),(11,'branding','0001_initial','2015-11-18 15:37:10.295010'),(12,'bulk_email','0001_initial','2015-11-18 15:37:10.849873'),(13,'bulk_email','0002_data__load_course_email_template','2015-11-18 15:37:10.939652'),(14,'certificates','0001_initial','2015-11-18 15:37:12.698538'),(15,'certificates','0002_data__certificatehtmlviewconfiguration_data','2015-11-18 15:37:12.746221'),(16,'certificates','0003_data__default_modes','2015-11-18 15:37:13.182516'),(17,'commerce','0001_data__add_ecommerce_service_user','2015-11-18 15:37:13.269990'),(18,'cors_csrf','0001_initial','2015-11-18 15:37:13.459604'),(19,'course_action_state','0001_initial','2015-11-18 15:37:14.011267'),(20,'course_groups','0001_initial','2015-11-18 15:37:15.487063'),(21,'course_modes','0001_initial','2015-11-18 15:37:15.719347'),(22,'course_overviews','0001_initial','2015-11-18 15:37:15.932886'),(23,'course_structures','0001_initial','2015-11-18 15:37:16.000954'),(24,'courseware','0001_initial','2015-11-18 15:37:18.771429'),(25,'credit','0001_initial','2015-11-18 15:37:21.519361'),(26,'dark_lang','0001_initial','2015-11-18 15:37:21.846133'),(27,'dark_lang','0002_data__enable_on_install','2015-11-18 15:37:21.995633'),(28,'default','0001_initial','2015-11-18 15:37:23.147337'),(29,'default','0002_add_related_name','2015-11-18 15:37:23.421429'),(30,'default','0003_alter_email_max_length','2015-11-18 15:37:23.512312'),(31,'django_comment_common','0001_initial','2015-11-18 15:37:24.320730'),(32,'django_notify','0001_initial','2015-11-18 15:37:25.685195'),(33,'django_openid_auth','0001_initial','2015-11-18 15:37:26.276837'),(34,'edx_proctoring','0001_initial','2015-11-18 15:37:30.965630'),(35,'edxval','0001_initial','2015-11-18 15:37:32.899299'),(36,'edxval','0002_data__default_profiles','2015-11-18 15:37:32.962490'),(37,'embargo','0001_initial','2015-11-18 15:37:34.781531'),(38,'embargo','0002_data__add_countries','2015-11-18 15:37:36.006428'),(39,'external_auth','0001_initial','2015-11-18 15:37:36.857447'),(40,'foldit','0001_initial','2015-11-18 15:37:38.106002'),(41,'instructor_task','0001_initial','2015-11-18 15:37:38.670378'),(42,'licenses','0001_initial','2015-11-18 15:37:39.225872'),(43,'lms_xblock','0001_initial','2015-11-18 15:37:39.674372'),(44,'milestones','0001_initial','2015-11-18 15:37:41.240336'),(45,'milestones','0002_data__seed_relationship_types','2015-11-18 15:37:41.287383'),(46,'mobile_api','0001_initial','2015-11-18 15:37:41.822343'),(47,'notes','0001_initial','2015-11-18 15:37:42.381389'),(48,'oauth2','0001_initial','2015-11-18 15:37:45.638217'),(49,'oauth2_provider','0001_initial','2015-11-18 15:37:46.173938'),(50,'oauth_provider','0001_initial','2015-11-18 15:37:47.398936'),(51,'organizations','0001_initial','2015-11-18 15:37:47.863329'),(52,'programs','0001_initial','2015-11-18 15:37:48.427080'),(53,'psychometrics','0001_initial','2015-11-18 15:37:48.987109'),(54,'self_paced','0001_initial','2015-11-18 15:37:49.523078'),(55,'sessions','0001_initial','2015-11-18 15:37:49.646106'),(56,'student','0001_initial','2015-11-18 15:38:05.543390'),(57,'shoppingcart','0001_initial','2015-11-18 15:38:21.727512'),(58,'sites','0001_initial','2015-11-18 15:38:21.837391'),(59,'splash','0001_initial','2015-11-18 15:38:23.244678'),(60,'status','0001_initial','2015-11-18 15:38:24.981737'),(61,'submissions','0001_initial','2015-11-18 15:38:26.499689'),(62,'survey','0001_initial','2015-11-18 15:38:28.962457'),(63,'teams','0001_initial','2015-11-18 15:38:31.641489'),(64,'third_party_auth','0001_initial','2015-11-18 15:38:35.861826'),(65,'track','0001_initial','2015-11-18 15:38:35.952939'),(66,'user_api','0001_initial','2015-11-18 15:38:42.846323'),(67,'util','0001_initial','2015-11-18 15:38:43.780691'),(68,'util','0002_data__default_rate_limit_config','2015-11-18 15:38:43.844470'),(69,'verify_student','0001_initial','2015-11-18 15:39:02.098134'),(70,'wiki','0001_initial','2015-11-18 15:39:50.801336'),(71,'workflow','0001_initial','2015-11-18 15:39:51.336698'),(72,'xblock_django','0001_initial','2015-11-18 15:39:52.487567'),(73,'contentstore','0001_initial','2015-11-18 15:40:36.154872'),(74,'course_creators','0001_initial','2015-11-18 15:40:36.715711'),(75,'xblock_config','0001_initial','2015-11-18 15:40:38.167185');
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

-- Dump completed on 2015-11-18 15:40:53
