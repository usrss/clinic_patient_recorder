-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: clinic_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `role` varchar(10) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `force_password_change` tinyint(1) NOT NULL,
  `failed_login_attempts` int unsigned NOT NULL,
  `locked_until` datetime(6) DEFAULT NULL,
  `reset_otp_expiry` datetime(6) DEFAULT NULL,
  `reset_otp` varchar(255) DEFAULT NULL,
  `profile_picture` varchar(100) DEFAULT NULL,
  `temp_password` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `accounts_user_email_b2644a56_uniq` (`email`),
  CONSTRAINT `accounts_user_chk_1` CHECK ((`failed_login_attempts` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user`
--

LOCK TABLES `accounts_user` WRITE;
/*!40000 ALTER TABLE `accounts_user` DISABLE KEYS */;
INSERT INTO `accounts_user` VALUES (1,'pbkdf2_sha256$1200000$EzGYQjweXIG94s28OcVZlg$TmKx3jE88s8r8UI0aG68qMl0rnra6myNdNo7qpIaTIQ=','2026-08-06 06:27:13.727006',1,'admin@norsuclinic','','','admin@gmail.com',1,0,'2026-07-17 03:43:30.899069','admin','',0,0,NULL,NULL,NULL,'',''),(3,'pbkdf2_sha256$1200000$ep1IJwsQO612xngCEJGYCB$ABKMpGISS0BjUjn0xp+PXYY3bS1lJsrYL7ITHIuPTS8=','2026-08-11 23:57:19.304247',0,'doctorr','EDALIN L.','DACULA, M.D., R.N.','bradicarcasona16@gmail.com',0,1,'2026-07-17 05:27:22.383479','doctor','',0,0,NULL,NULL,NULL,'staff/Cat.jfif','2125'),(4,'pbkdf2_sha256$1200000$mEraOp83FYHLN1trZfYW4S$N48bJUZFaJ0e4EGKqBMefLpfQDTQZIJ9i6LnZezVgAM=','2026-08-11 09:48:29.693271',0,'frontdesk','Sample','User',NULL,0,1,'2026-07-17 05:29:18.362534','frontdesk','',0,0,NULL,NULL,NULL,'','9765'),(6,'pbkdf2_sha256$1200000$Smzoe9fp6XdXXmCIgRh937$9HkBR5w6uVec1ErVWvKExyv5c7/Nnv8podiKjFzgfFU=','2026-08-11 09:52:44.960990',0,'202301028','BRADI','CARCASONA','carcasonabradi@gmail.com',0,1,'2026-07-17 05:45:50.586987','patient','',0,0,NULL,'2026-07-28 06:47:04.472974','pbkdf2_sha256$1200000$pXkQCVdTBiwyKTQGdYAzOX$F3CjfJfqnKUbhTery1mXsuHOrzj67UQMoGljJIx1SCE=','',''),(7,'pbkdf2_sha256$1200000$w2oPWcFqi1ViyzhWClAeAF$XOCv2xgtl3boURPNn5WYnFvXl5ULTQTt3dSQ3G1FziU=','2026-08-11 09:49:34.641147',0,'202300316','Adrian','Paylande','sample@gmail.com',0,1,'2026-07-21 02:29:32.114035','patient','',0,0,NULL,NULL,NULL,'',''),(12,'pbkdf2_sha256$1200000$lcdtCQtCMEELaKGxz9OfV8$EAueT5mf+nH0l0008OPAL6yOlliumUxwkp65b7UP/EA=','2026-07-29 06:18:43.534834',0,'202300055','Kylle','Acibron','kylleacibron@gmail.com',0,1,'2026-07-29 05:23:31.015816','patient','09455470173',0,0,NULL,NULL,NULL,'',''),(13,'pbkdf2_sha256$1200000$6cjQk7RaL9RNztPcWXJUog$2TYmTd92nT3xXP2Wxm7TzUNY/pflzOKHUPtznA/C4/Y=','2026-08-12 00:08:14.682136',1,'adminclinic','NORSU','Admin','norsuclinic1@gmail.com',1,1,'2026-07-29 05:31:04.355165','admin','',0,0,NULL,NULL,NULL,'staff/cat_zJxegMk.jpg',''),(14,'pbkdf2_sha256$1200000$rgmRxWGzZP8eYYQn59usXU$gQkEg5Z9OZakVOSS4CtQ1Q0CCAquJ1OXG3xhC12RWIg=','2026-07-29 05:51:39.487407',0,'202300627','Kristel May','Baga-an','bagaankristelmay@gmail.com',0,1,'2026-07-29 05:51:39.058313','patient','09354628604',0,0,NULL,NULL,NULL,'',''),(15,'pbkdf2_sha256$1200000$fLqZETXe7RIDNOwTOQuZaw$PIxoioxaWIaUaE28BO1VMkP2E07yil6N1LhNcFTD8V4=','2026-07-30 03:46:40.016656',0,'12345678','Bradi','Carcasona','bradicarcasona21@gmail.com',0,1,'2026-07-30 03:46:39.679746','patient','09690956344',0,0,NULL,NULL,NULL,'',''),(16,'pbkdf2_sha256$1200000$i6yaEVN2D9NxI51WArgXd9$lJlI9W+Vpd2YcmWtOgyXLJtBhs5Jtx7lezJ0YDYb60g=','2026-07-30 03:49:03.605922',0,'87654321','Bradi','Carcasona','bradicarcasona20@gmail.com',0,1,'2026-07-30 03:49:03.256076','patient','09690956344',0,0,NULL,NULL,NULL,'','');
/*!40000 ALTER TABLE `accounts_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_groups`
--

LOCK TABLES `accounts_user_groups` WRITE;
/*!40000 ALTER TABLE `accounts_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_user_permissions`
--

LOCK TABLES `accounts_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs_auditlog`
--

DROP TABLE IF EXISTS `audit_logs_auditlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs_auditlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_role` varchar(20) NOT NULL,
  `user_name` varchar(200) NOT NULL,
  `action` varchar(20) NOT NULL,
  `module` varchar(30) NOT NULL,
  `description` longtext NOT NULL,
  `object_model` varchar(100) NOT NULL,
  `object_id` varchar(50) NOT NULL,
  `object_repr` varchar(300) NOT NULL,
  `changes_before` json DEFAULT NULL,
  `changes_after` json DEFAULT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `audit_logs_auditlog_action_d8830a83` (`action`),
  KEY `audit_logs_auditlog_module_147c7242` (`module`),
  KEY `audit_logs_auditlog_status_50c30a06` (`status`),
  KEY `audit_logs_auditlog_timestamp_e936ec2d` (`timestamp`),
  KEY `audit_logs__timesta_63825c_idx` (`timestamp` DESC),
  KEY `audit_logs__user_id_64dfe5_idx` (`user_id`,`timestamp` DESC),
  KEY `audit_logs__user_ro_66e0c7_idx` (`user_role`,`timestamp` DESC),
  KEY `audit_logs__action_6eaf81_idx` (`action`,`module`),
  KEY `audit_logs__module_7b7e44_idx` (`module`,`timestamp` DESC),
  KEY `audit_logs__status_bdfe51_idx` (`status`,`timestamp` DESC),
  KEY `audit_logs__object__535fa7_idx` (`object_model`,`object_id`),
  CONSTRAINT `audit_logs_auditlog_user_id_64263a1c_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=406 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs_auditlog`
--

LOCK TABLES `audit_logs_auditlog` WRITE;
/*!40000 ALTER TABLE `audit_logs_auditlog` DISABLE KEYS */;
INSERT INTO `audit_logs_auditlog` VALUES (1,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:43:56.333275',1),(2,'admin','admin@norsuclinic','CREATE','User Management','Created staff account — Sample User (patient)','accounts.User','2','Sample User (patient)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:44:49.915798',1),(3,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:45:15.895143',1),(4,'patient','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:45:22.283586',NULL),(5,'patient','Sample User','UPDATE','Authentication','Password changed — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:45:37.007808',NULL),(6,'patient','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:45:47.891562',NULL),(7,'patient','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 03:45:57.255533',NULL),(8,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:11:19.054561',1),(9,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:14:44.140953',1),(10,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:21:37.364287',1),(11,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:22:38.287886',1),(12,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:23:38.210965',1),(13,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:24:38.269428',1),(14,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:26:56.274945',1),(15,'admin','admin@norsuclinic','CREATE','User Management','Created staff account — BRADI CARCASONA (doctor)','accounts.User','3','BRADI CARCASONA (doctor)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:27:22.886984',1),(16,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:27:38.559118',1),(17,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:27:43.877310',3),(18,'doctor','BRADI CARCASONA','UPDATE','Authentication','Password changed — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:28:03.424812',3),(19,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:28:30.539592',3),(20,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:28:48.794887',1),(21,'admin','admin@norsuclinic','CREATE','User Management','Created staff account — Sample User (frontdesk)','accounts.User','4','Sample User (frontdesk)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:29:18.818525',1),(22,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:29:47.614357',1),(23,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:29:56.037814',4),(24,'frontdesk','Sample User','UPDATE','Authentication','Password changed — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:30:09.866605',4),(25,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:43:24.991035',4),(26,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:43:46.640802',1),(27,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:44:45.775146',1),(28,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:44:53.304975',4),(29,'frontdesk','Sample User','CREATE','Consultations','Created consultation for new patient — BRADI CARCASONA','consultations.Consultation','1','Consultation #1 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:45:51.005909',4),(30,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #1 — queued for triage','consultations.Consultation','1','Consultation #1 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','172.18.0.1','SUCCESS','2026-07-17 05:46:10.464802',4),(31,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:46:30.663870',4),(32,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:46:35.857033',6),(33,'patient','BRADI CARCASONA','UPDATE','Authentication','Password changed — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:47:10.139951',6),(34,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:48:22.611367',6),(35,'patient','BRADI CARCASONA','LOGIN','Authentication','Failed login attempt — 202301028','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-17 05:48:31.036467',6),(36,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:48:36.958356',6),(37,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:48:44.609135',6),(38,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:49:03.350713',1),(39,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:49:09.934165',1),(40,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:49:19.881123',3),(41,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Low urgency','consultations.Consultation','1','Consultation #1 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"low\"}','172.18.0.1','SUCCESS','2026-07-17 05:50:01.420907',3),(42,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #1 — no follow-up needed','consultations.Consultation','1','Consultation #1 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-17 05:50:23.250832',3),(43,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft fit_to_work certificate — BRADI CARCASONA','certificates.MedicalCertificate','1','Medical Certificate-OJT #1 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-17 05:50:31.468706',3),(44,'admin','admin@norsuclinic','LOGIN','Authentication','Failed login attempt — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-21 00:06:45.804810',1),(45,'admin','admin@norsuclinic','LOGIN','Authentication','Failed login attempt — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-21 00:07:00.927411',1),(46,'admin','admin@norsuclinic','LOGIN','Authentication','Failed login attempt — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-21 00:07:14.739150',1),(47,'admin','admin@norsuclinic','LOGIN','Authentication','Failed login attempt — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-21 00:07:29.150645',1),(48,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 00:15:29.836524',1),(49,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 00:15:46.541045',1),(50,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 00:16:13.571279',1),(51,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 00:16:24.353378',4),(52,'frontdesk','Sample User','CREATE','Consultations','Created consultation for new patient — Adrian Paylande','consultations.Consultation','2','Consultation #2 — Adrian Paylande (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:29:32.510277',4),(53,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #2 — queued for triage','consultations.Consultation','2','Consultation #2 — Adrian Paylande (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','172.18.0.1','SUCCESS','2026-07-21 02:29:59.262734',4),(54,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:30:02.623156',4),(55,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:30:09.286727',3),(56,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — Adrian Paylande — Medium urgency','consultations.Consultation','2','Consultation #2 — Adrian Paylande (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-21 02:30:37.911861',3),(57,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #2 — follow-up recommended','consultations.Consultation','2','Consultation #2 — Adrian Paylande (Active - Follow-up)',NULL,'{\"status\": \"active_follow_up\"}','172.18.0.1','SUCCESS','2026-07-21 02:31:06.755541',3),(58,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft standard certificate — Adrian Paylande','certificates.MedicalCertificate','2','Medical Certificate-Absences  of classes-work #2 — Adrian Paylande',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:31:11.245537',3),(59,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft fit_to_work certificate — Adrian Paylande','certificates.MedicalCertificate','3','Medical Certificate-OJT #3 — Adrian Paylande',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:31:47.982981',3),(60,'doctor','BRADI CARCASONA','VIEW','Patients','Viewed patient record — Adrian Paylande (202300316)','patients.Patient','3','202300316 — Adrian Paylande',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 02:47:28.436635',3),(61,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 06:40:36.335115',3),(62,'patient','BRADI CARCASONA','LOGIN','Authentication','Failed login attempt — 202301028','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-21 06:40:47.497596',6),(63,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 06:40:53.354378',6),(64,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 06:41:34.639423',6),(65,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 06:41:44.762644',1),(66,'admin','admin@norsuclinic','UPDATE','Settings','Updated academic year archive settings','patients.AcademicYearSettings','1','Academic Year ends May 30, 2026 — Archive after 5 months','{\"academic_year_end\": \"2026-05-31\", \"archive_after_months\": 5}','{\"academic_year_end\": \"2026-05-30\", \"archive_after_months\": 5}','172.18.0.1','SUCCESS','2026-07-21 06:41:57.503551',1),(67,'admin','admin@norsuclinic','UPDATE','Settings','Updated academic year archive settings','patients.AcademicYearSettings','1','Academic Year ends August 31, 2026 — Archive after 5 months','{\"academic_year_end\": \"2026-05-30\", \"archive_after_months\": 5}','{\"academic_year_end\": \"2026-08-31\", \"archive_after_months\": 5}','172.18.0.1','SUCCESS','2026-07-21 06:42:40.527855',1),(68,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:11:42.153382',1),(69,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:11:51.741148',6),(70,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:16:32.443543',6),(71,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:16:43.141847',1),(72,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:16:59.487511',1),(73,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-21 07:26:09.620348',1),(74,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:32:05.788547',1),(75,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:32:10.476132',1),(76,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:33:42.608979',1),(77,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:44:37.755166',1),(78,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:44:46.724305',1),(79,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:44:56.766757',1),(80,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:46:31.411450',6),(81,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','7','Consultation #7 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:46:52.446203',6),(82,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:46:59.879420',6),(83,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:47:06.140486',4),(84,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #7 — queued for triage','consultations.Consultation','7','Consultation #7 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','172.18.0.1','SUCCESS','2026-07-23 01:47:16.128683',4),(85,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:47:19.765840',4),(86,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:47:27.919382',3),(87,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','7','Consultation #7 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-23 01:47:50.500630',3),(88,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #7 — no follow-up needed','consultations.Consultation','7','Consultation #7 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-23 01:48:06.990196',3),(89,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft fit_to_work certificate — BRADI CARCASONA','certificates.MedicalCertificate','16','Medical Certificate — OJT (Fit to Work) #16 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:49:01.770246',3),(90,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:51:24.013287',3),(91,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 01:51:32.331457',6),(92,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:32:47.380777',6),(93,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:32:54.632212',6),(94,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','8','Consultation #8 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:33:22.882186',6),(95,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:33:32.899674',6),(96,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:33:38.921927',4),(97,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #8 — queued for triage','consultations.Consultation','8','Consultation #8 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 2}','172.18.0.1','SUCCESS','2026-07-23 03:33:49.992790',4),(98,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:33:53.465811',4),(99,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:34:04.205395',3),(100,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','8','Consultation #8 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-23 03:34:39.491957',3),(101,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #8 — no follow-up needed','consultations.Consultation','8','Consultation #8 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-23 03:35:01.500051',3),(102,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft fit_to_work certificate — BRADI CARCASONA','certificates.MedicalCertificate','17','Medical Certificate — OJT (Fit to Work) #17 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:35:09.915674',3),(103,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:44:06.345952',3),(104,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:44:12.476414',6),(105,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','9','Consultation #9 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:44:27.247214',6),(106,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:44:34.966841',6),(107,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:44:42.278505',4),(108,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #9 — queued for triage','consultations.Consultation','9','Consultation #9 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 3}','172.18.0.1','SUCCESS','2026-07-23 03:44:55.824968',4),(109,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:45:01.087738',4),(110,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:45:13.806961',3),(111,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','9','Consultation #9 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-23 03:45:42.145500',3),(112,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #9 — no follow-up needed','consultations.Consultation','9','Consultation #9 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-23 03:46:01.902923',3),(113,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft standard certificate — BRADI CARCASONA','certificates.MedicalCertificate','18','Medical Certificate — Absences (Classes/Work) #18 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 03:46:14.178504',3),(114,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:31:08.623689',3),(115,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:31:18.230855',6),(116,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','10','Consultation #10 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:31:39.741354',6),(117,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:31:48.048405',6),(118,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:31:57.723753',4),(119,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #10 — queued for triage','consultations.Consultation','10','Consultation #10 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 4}','172.18.0.1','SUCCESS','2026-07-23 04:32:07.066629',4),(120,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:32:11.496658',4),(121,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:32:20.175146',3),(122,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','10','Consultation #10 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-23 04:32:42.952477',3),(123,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #10 — no follow-up needed','consultations.Consultation','10','Consultation #10 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-23 04:32:57.635667',3),(124,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft ojt certificate — BRADI CARCASONA','certificates.MedicalCertificate','19','Medical Certificate — OJT #19 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-23 04:51:13.218973',3),(125,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 00:46:50.051701',1),(126,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 00:46:54.908174',1),(127,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:27:56.520649',1),(128,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:43:37.393377',1),(129,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:43:49.433925',6),(130,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:44:04.248690',6),(131,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:44:17.885470',6),(132,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:44:28.879585',6),(133,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:44:36.318956',6),(134,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:58:17.801625',6),(135,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 01:58:24.536146',6),(136,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:06:09.451365',6),(137,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:06:19.477345',6),(138,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:06:34.783025',6),(139,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:06:44.670663',1),(140,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:18:43.053422',1),(141,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:18:51.237563',6),(142,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:19:39.039744',6),(143,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:19:46.999991',6),(144,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:44:36.744205',6),(145,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:44:51.000422',6),(146,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:44:59.098748',6),(147,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:47:38.213277',6),(148,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:48:09.152525',6),(149,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 05:51:46.437046',6),(150,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:05:22.935848',6),(151,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:07:51.610211',6),(152,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:08:11.703927',6),(153,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:09:06.488275',6),(154,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:09:33.653474',6),(155,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:14:18.310822',6),(156,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:16:57.175053',6),(157,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:17:07.403265',6),(158,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:19:24.598629',6),(159,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:19:35.151642',6),(160,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:19:43.954867',6),(161,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:19:51.797272',4),(162,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:20:17.408748',4),(163,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:22:42.476671',4),(164,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:23:02.071057',4),(165,'admin','admin@norsuclinic','LOGIN','Authentication','Successful login — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:23:11.791988',1),(166,'admin','admin@norsuclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:23:26.213970',1),(167,'admin','admin@norsuclinic','LOGOUT','Authentication','Logout — admin@norsuclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:23:36.210507',1),(168,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:26:31.091813',6),(169,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-28 06:26:45.914483',6),(170,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 05:10:08.021110',6),(171,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 05:10:20.035184',6),(172,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 05:10:27.426388',4),(173,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:18:54.229006',6),(174,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:20:39.495300',6),(175,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 05:31:26.824049',13),(176,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 05:31:34.718440',13),(177,'admin','adminclinic','UPDATE','User Management','Deactivated account — admin@norsuclinic','accounts.User','1','admin@norsuclinic (admin)','{\"is_active\": true}','{\"is_active\": false}','103.105.214.136','SUCCESS','2026-07-29 05:31:52.817074',13),(178,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 05:41:20.321284',13),(179,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 05:47:18.869759',13),(180,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 05:47:39.120215',13),(181,'patient','Kristel May Baga-an','CREATE','Consultations','Submitted new consultation request — Kristel May Baga-an','consultations.Consultation','11','Consultation #11 — Kristel May Baga-an (Pending)',NULL,NULL,'103.68.156.14','SUCCESS','2026-07-29 05:52:25.546329',14),(182,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:53:08.134881',13),(183,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:53:17.780879',4),(184,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #11 — queued for triage','consultations.Consultation','11','Consultation #11 — Kristel May Baga-an (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','103.105.214.138','SUCCESS','2026-07-29 05:53:38.437960',4),(185,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:53:44.212699',4),(186,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:53:59.138245',3),(187,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — Kristel May Baga-an — Medium urgency','consultations.Consultation','11','Consultation #11 — Kristel May Baga-an (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','103.105.214.138','SUCCESS','2026-07-29 05:54:33.458963',3),(188,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #11 — no follow-up needed','consultations.Consultation','11','Consultation #11 — Kristel May Baga-an (Completed)',NULL,'{\"status\": \"completed\"}','103.105.214.138','SUCCESS','2026-07-29 05:55:17.373670',3),(189,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft absences certificate — Kristel May Baga-an','certificates.MedicalCertificate','20','Medical Certificate — Absences (Classes/Work) #20 — Kristel May Baga-an',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 05:55:38.169909',3),(190,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:01:16.168644',3),(191,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:01:27.258658',13),(192,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:06:29.969572',13),(193,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:07:31.580614',13),(194,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:08:31.604477',13),(195,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:09:31.605378',13),(196,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:10:31.567132',13),(197,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:11:31.997048',13),(198,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:12:16.446764',13),(199,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:12:30.961268',13),(200,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:13:29.727555',13),(201,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:14:31.918197',13),(202,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:15:31.573061',13),(203,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:16:13.506861',13),(204,'patient','Kylle Acibron','LOGIN','Authentication','Successful login — Kylle Acibron','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-29 06:18:43.520721',12),(205,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:19:53.997400',13),(206,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:20:43.282185',13),(207,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:20:46.900081',13),(208,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:20:50.957400',13),(209,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:20:56.270338',13),(210,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:21:00.283246',13),(211,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-29 06:22:03.355132',13),(212,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 08:33:18.851796',13),(213,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 08:33:25.106716',13),(214,'admin','adminclinic','EXPORT','Reports','Exported full diagnosis report as PDF (section=all)','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 08:33:40.105260',13),(215,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 08:44:37.305535',13),(216,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:06:46.276841',13),(217,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:06:53.435954',6),(218,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','12','Consultation #12 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:07:23.632772',6),(219,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:07:30.048819',6),(220,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:07:37.414523',4),(221,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #12 — queued for triage','consultations.Consultation','12','Consultation #12 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 2}','172.18.0.1','SUCCESS','2026-07-29 09:07:52.728344',4),(222,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:07:56.141007',4),(223,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:08:02.658405',3),(224,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','12','Consultation #12 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-07-29 09:08:32.261984',3),(225,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #12 — no follow-up needed','consultations.Consultation','12','Consultation #12 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-07-29 09:08:46.162323',3),(226,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft absences certificate — BRADI CARCASONA','certificates.MedicalCertificate','21','Medical Certificate — Absences (Classes/Work) #21 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:08:50.099384',3),(227,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:18:07.957273',3),(228,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:41:17.672656',13),(229,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:41:28.583259',13),(230,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:41:28.922414',13),(231,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:41:35.286901',13),(232,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:42:08.695756',13),(233,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:48:12.747462',13),(234,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:48:18.606786',13),(235,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:48:23.686572',13),(236,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-29 09:48:32.024354',6),(237,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:25:57.060931',6),(238,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:34:16.150438',6),(239,'admin','adminclinic','LOGIN','Authentication','Failed login attempt — adminclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-30 00:34:30.717104',13),(240,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:34:42.357172',13),(241,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:34:49.714401',13),(242,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:34:56.671995',13),(243,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:36:00.008602',13),(244,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:40:23.634713',6),(245,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 00:54:30.817032',6),(246,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 01:06:08.837315',6),(247,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 01:06:32.683934',6),(248,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 03:07:19.563304',6),(249,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 03:10:10.871724',6),(250,'patient','Bradi Carcasona','LOGOUT','Authentication','Logout — Bradi Carcasona','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 03:46:58.336282',15),(251,'patient','Bradi Carcasona','LOGOUT','Authentication','Logout — Bradi Carcasona','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 03:49:49.383144',16),(252,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.140','SUCCESS','2026-07-30 04:03:57.493805',6),(253,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.140','SUCCESS','2026-07-30 04:04:18.576508',6),(254,'admin','adminclinic','LOGIN','Authentication','Failed login attempt — adminclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-30 04:44:14.838519',13),(255,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:45:53.256413',13),(256,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:45:59.429627',13),(257,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:47:10.253372',13),(258,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:47:45.948725',13),(259,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:47:51.983055',13),(260,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 04:47:56.272023',13),(261,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:02:13.830295',13),(262,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:02:46.540362',13),(263,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:03:00.587713',13),(264,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:08:39.605139',13),(265,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:08:44.613024',13),(266,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:08:52.229382',13),(267,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:08:58.166397',13),(268,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:09:02.242947',13),(269,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:09:12.293666',6),(270,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:37:27.437457',6),(271,'admin','adminclinic','LOGIN','Authentication','Failed login attempt — adminclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-07-30 05:37:35.616283',13),(272,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:37:43.810084',13),(273,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:37:50.379012',13),(274,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:38:05.435330',13),(275,'admin','adminclinic','VIEW','Patients','Viewed patient record — Adrian Paylande (202300316)','patients.Patient','3','202300316 — Adrian Paylande',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:38:35.556863',13),(276,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:40:18.086612',13),(277,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 05:40:26.221202',6),(278,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:02:19.859164',6),(279,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:02:27.735658',13),(280,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:02:40.967072',13),(281,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:07:59.817915',13),(282,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:08:47.448835',13),(283,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:08:55.444585',13),(284,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:09:55.867690',13),(285,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:10:55.858534',13),(286,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:11:55.861581',13),(287,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:12:18.793603',13),(288,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 06:12:23.593059',13),(289,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 06:18:07.710743',13),(290,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 06:18:11.057363',13),(291,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 06:18:15.443483',13),(292,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.138','SUCCESS','2026-07-30 06:21:13.326506',6),(293,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','13','Consultation #13 — BRADI CARCASONA (Pending)',NULL,NULL,'175.176.66.68','SUCCESS','2026-07-30 06:44:01.092777',6),(294,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'175.176.66.68','SUCCESS','2026-07-30 06:44:26.563230',6),(295,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'175.176.66.68','SUCCESS','2026-07-30 06:44:38.725861',4),(296,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #13 — queued for triage','consultations.Consultation','13','Consultation #13 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','175.176.66.68','SUCCESS','2026-07-30 06:44:54.266156',4),(297,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'175.176.66.68','SUCCESS','2026-07-30 06:44:59.385816',4),(298,'doctor','BRADI CARCASONA','LOGIN','Authentication','Failed login attempt — doctorr','','','',NULL,NULL,'175.176.66.68','FAILED','2026-07-30 06:45:11.104537',3),(299,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'175.176.66.68','SUCCESS','2026-07-30 06:45:22.352515',3),(300,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 07:03:18.685592',6),(301,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 07:03:29.215716',6),(302,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-07-30 07:03:56.509715',6),(303,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 07:04:12.692356',13),(304,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 07:04:16.136813',13),(305,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'103.105.214.136','SUCCESS','2026-07-30 07:04:35.603582',13),(306,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'103.105.214.137','SUCCESS','2026-07-30 08:43:53.722393',13),(307,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'103.105.214.137','SUCCESS','2026-07-30 08:44:12.407635',13),(308,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'103.105.214.137','SUCCESS','2026-07-30 08:44:20.272617',13),(309,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:36:18.176484',13),(310,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:36:24.202181',13),(311,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:36:49.500610',13),(312,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:38:12.522177',13),(313,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:38:16.003415',13),(314,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:44:59.386738',13),(315,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 04:45:07.288967',6),(316,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 05:29:14.280020',6),(317,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 05:29:19.111307',6),(318,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 05:29:26.878212',4),(319,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #14 — queued for triage','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','172.18.0.1','SUCCESS','2026-08-06 05:29:36.395783',4),(320,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 05:29:40.601152',4),(321,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 05:29:49.528419',3),(322,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Low urgency','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"low\"}','172.18.0.1','SUCCESS','2026-08-06 05:30:33.790583',3),(323,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Low urgency','consultations.Consultation','13','Consultation #13 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"low\"}','172.18.0.1','SUCCESS','2026-08-06 06:08:15.602878',3),(324,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #13 — no follow-up needed','consultations.Consultation','13','Consultation #13 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-08-06 06:09:32.243053',3),(325,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:10:18.744107',3),(326,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:10:25.756422',6),(327,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','15','Consultation #15 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:11:41.400489',6),(328,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:11:46.212229',6),(329,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:11:53.699599',4),(330,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #15 — queued for triage','consultations.Consultation','15','Consultation #15 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 2}','172.18.0.1','SUCCESS','2026-08-06 06:12:06.344761',4),(331,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:12:10.972730',4),(332,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:12:18.681363',3),(333,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Medium urgency','consultations.Consultation','15','Consultation #15 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"medium\"}','172.18.0.1','SUCCESS','2026-08-06 06:12:42.712479',3),(334,'doctor','BRADI CARCASONA','UPDATE','Consultations','Amended triage for consultation #14 — Verification: reworded chief complaint, re-checked pulse','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Triaged)',NULL,'{\"notes\": \"[Amended by doctorr: Verification: reworded chief complaint, re-checked pulse]\", \"chief_complaint\": \"abdominal pain\"}','127.0.0.1','SUCCESS','2026-08-06 06:26:36.932097',3),(335,'doctor','BRADI CARCASONA','UPDATE','Consultations','Amended triage for consultation #14 — wrong value','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Triaged)','{\"notes\": \"[Amended by doctorr: Verification: reworded chief complaint, re-checked pulse]\", \"chief_complaint\": \"abdominal pain\"}','{\"notes\": \"ala lang\\n\\n[Amended by doctorr: wrong value]\", \"chief_complaint\": \"nahh\"}','172.18.0.1','SUCCESS','2026-08-06 06:27:08.389697',3),(336,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:27:12.395899',3),(337,'admin','adminclinic','LOGIN','Authentication','Failed login attempt — adminclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-08-06 06:27:19.111380',13),(338,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-06 06:27:25.696047',13),(339,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 00:37:25.295861',6),(340,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:08:57.469068',6),(341,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:09:09.010436',3),(342,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #14 — no follow-up needed','consultations.Consultation','14','Consultation #14 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-08-07 01:09:41.042441',3),(343,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft absences certificate — BRADI CARCASONA','certificates.MedicalCertificate','22','Medical Certificate — Absences (Classes/Work) #22 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:09:46.787710',3),(344,'doctor','BRADI CARCASONA','DELETE','Medical Certificates','Discarded draft certificate — BRADI CARCASONA','certificates.MedicalCertificate','22','Medical Certificate — Absences (Classes/Work) #22 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:10:30.957632',3),(345,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft ojt certificate — BRADI CARCASONA','certificates.MedicalCertificate','23','Medical Certificate — OJT #23 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:17:34.861682',3),(346,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:18:05.043897',3),(347,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:18:12.587903',6),(348,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:21:49.306833',6),(349,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:22:03.843806',13),(350,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:22:09.438284',13),(351,'admin','adminclinic','EXPORT','Reports','Exported full diagnosis report as PDF (section=diagnoses)','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:22:20.876175',13),(352,'admin','adminclinic','EXPORT','Reports','Exported full diagnosis report as PDF (section=all)','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:25:54.379018',13),(353,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:26:50.621068',13),(354,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:26:59.830758',13),(355,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:27:50.829654',13),(356,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:32:03.466507',13),(357,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:32:10.805225',6),(358,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:32:22.548900',6),(359,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:32:34.887758',3),(360,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #15 — no follow-up needed','consultations.Consultation','15','Consultation #15 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-08-07 01:33:00.833928',3),(361,'doctor','BRADI CARCASONA','VIEW','Patients','Viewed patient record — BRADI CARCASONA (202301028)','patients.Patient','2','202301028 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 01:33:48.580723',3),(362,'doctor','BRADI CARCASONA','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:03:47.702032',3),(363,'doctor','BRADI CARCASONA','VIEW','Patients','Viewed patient record — BRADI CARCASONA (202301028)','patients.Patient','2','202301028 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:03:58.647859',3),(364,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:06:38.011375',3),(365,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:06:50.180312',6),(366,'patient','BRADI CARCASONA','CREATE','Consultations','Submitted new consultation request — BRADI CARCASONA','consultations.Consultation','16','Consultation #16 — BRADI CARCASONA (Pending)',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:07:12.981098',6),(367,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:07:18.406671',6),(368,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:07:24.611098',4),(369,'frontdesk','Sample User','UPDATE','Consultations','Processed consultation #16 — queued for triage','consultations.Consultation','16','Consultation #16 — BRADI CARCASONA (Queued)',NULL,'{\"status\": \"queued\", \"queue_number\": 1}','172.18.0.1','SUCCESS','2026-08-07 02:07:32.609121',4),(370,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:07:35.720362',4),(371,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:07:42.211678',3),(372,'doctor','BRADI CARCASONA','UPDATE','Consultations','Triaged patient — BRADI CARCASONA — Low urgency','consultations.Consultation','16','Consultation #16 — BRADI CARCASONA (Triaged)',NULL,'{\"status\": \"triaged\", \"urgency\": \"low\"}','172.18.0.1','SUCCESS','2026-08-07 02:08:33.384834',3),(373,'doctor','BRADI CARCASONA','UPDATE','Consultations','Amended prescription for consultation #16 — BRADI CARCASONA','consultations.Prescription','16','Prescription #16 — Consultation #16','{\"items\": [], \"diagnosis\": \"oks\", \"treatment_plan\": \"nah\"}','{\"items\": [], \"diagnosis\": \"okss\", \"treatment_plan\": \"nah\"}','172.18.0.1','SUCCESS','2026-08-07 02:14:21.288452',3),(374,'doctor','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-07 02:15:09.058518',3),(375,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:46:54.317249',13),(376,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:46:59.046155',13),(377,'admin','adminclinic','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:47:04.720618',13),(378,'admin','adminclinic','EXPORT','Reports','Exported feedback report as PDF','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:47:46.767656',13),(379,'admin','adminclinic','LOGOUT','Authentication','Logout — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:48:19.151181',13),(380,'frontdesk','Sample User','LOGIN','Authentication','Successful login — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:48:29.680503',4),(381,'frontdesk','Sample User','LOGOUT','Authentication','Logout — Sample User','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:49:29.023838',4),(382,'patient','Adrian Paylande','LOGIN','Authentication','Successful login — Adrian Paylande','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:49:34.632991',7),(383,'patient','Adrian Paylande','UPDATE','Authentication','Password changed — Adrian Paylande','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:50:03.399246',7),(384,'patient','Adrian Paylande','LOGOUT','Authentication','Logout — Adrian Paylande','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:52:35.254764',7),(385,'patient','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:52:44.949355',6),(386,'patient','BRADI CARCASONA','LOGOUT','Authentication','Logout — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:53:48.257232',6),(387,'doctor','BRADI CARCASONA','LOGIN','Authentication','Successful login — BRADI CARCASONA','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:53:56.413163',3),(388,'doctor','BRADI CARCASONA','UPDATE','Consultations','Amended prescription for consultation #16 — BRADI CARCASONA','consultations.Prescription','16','Prescription #16 — Consultation #16','{\"items\": [], \"diagnosis\": \"okss\", \"treatment_plan\": \"nah\"}','{\"items\": [], \"diagnosis\": \"okss\", \"treatment_plan\": \"nah\"}','172.18.0.1','SUCCESS','2026-08-11 09:54:22.003489',3),(389,'doctor','BRADI CARCASONA','UPDATE','Consultations','Completed consultation #16 — no follow-up needed','consultations.Consultation','16','Consultation #16 — BRADI CARCASONA (Completed)',NULL,'{\"status\": \"completed\"}','172.18.0.1','SUCCESS','2026-08-11 09:54:28.363208',3),(390,'doctor','BRADI CARCASONA','CREATE','Medical Certificates','Created draft ojt certificate — BRADI CARCASONA','certificates.MedicalCertificate','24','Medical Certificate — OJT #24 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:54:32.246840',3),(391,'doctor','EDALIN L. DACULA, M.D., R.N.','LOGOUT','Authentication','Logout — EDALIN L. DACULA, M.D., R.N.','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:57:31.609584',3),(392,'admin','adminclinic','LOGIN','Authentication','Successful login — adminclinic','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:57:42.169267',13),(393,'admin','adminclinic','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:57:58.495916',13),(394,'admin','NORSU Admin','LOGOUT','Authentication','Logout — NORSU Admin','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 09:59:07.597099',13),(395,'admin','NORSU Admin','LOGIN','Authentication','Successful login — NORSU Admin','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:51:20.276840',13),(396,'admin','NORSU Admin','VIEW','Reports','Viewed report dashboard','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:56:37.889973',13),(397,'admin','NORSU Admin','LOGOUT','Authentication','Logout — NORSU Admin','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:57:07.056938',13),(398,'doctor','EDALIN L. DACULA, M.D., R.N.','LOGIN','Authentication','Successful login — EDALIN L. DACULA, M.D., R.N.','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:57:19.271381',3),(399,'doctor','EDALIN L. DACULA, M.D., R.N.','VIEW','Patients','Viewed patient record — Kylle Ian Dicen Acibron (202300055)','patients.Patient','8','202300055 — Kylle Ian Dicen Acibron',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:57:26.031656',3),(400,'doctor','EDALIN L. DACULA, M.D., R.N.','VIEW','Patients','Viewed patient record — Kristel May Baga-an (202300627)','patients.Patient','9','202300627 — Kristel May Baga-an',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:57:31.460776',3),(401,'doctor','EDALIN L. DACULA, M.D., R.N.','VIEW','Patients','Viewed patient record — BRADI CARCASONA (202301028)','patients.Patient','2','202301028 — BRADI CARCASONA',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-11 23:57:41.037843',3),(402,'doctor','EDALIN L. DACULA, M.D., R.N.','LOGOUT','Authentication','Logout — EDALIN L. DACULA, M.D., R.N.','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-12 00:07:48.899195',3),(403,'admin','NORSU Admin','LOGIN','Authentication','Failed login attempt — adminclinic','','','',NULL,NULL,'172.18.0.1','FAILED','2026-08-12 00:08:04.922332',13),(404,'admin','NORSU Admin','LOGIN','Authentication','Successful login — NORSU Admin','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-12 00:08:14.647940',13),(405,'admin','NORSU Admin','LOGOUT','Authentication','Logout — NORSU Admin','','','',NULL,NULL,'172.18.0.1','SUCCESS','2026-08-12 00:08:33.625850',13);
/*!40000 ALTER TABLE `audit_logs_auditlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=153 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add User',6,'add_user'),(22,'Can change User',6,'change_user'),(23,'Can delete User',6,'delete_user'),(24,'Can view User',6,'view_user'),(25,'Can add Patient',8,'add_patient'),(26,'Can change Patient',8,'change_patient'),(27,'Can delete Patient',8,'delete_patient'),(28,'Can view Patient',8,'view_patient'),(29,'Can add Patient Profile',9,'add_patientprofile'),(30,'Can change Patient Profile',9,'change_patientprofile'),(31,'Can delete Patient Profile',9,'delete_patientprofile'),(32,'Can view Patient Profile',9,'view_patientprofile'),(33,'Can add Academic Year Settings',7,'add_academicyearsettings'),(34,'Can change Academic Year Settings',7,'change_academicyearsettings'),(35,'Can delete Academic Year Settings',7,'delete_academicyearsettings'),(36,'Can view Academic Year Settings',7,'view_academicyearsettings'),(37,'Can add Consultation',11,'add_consultation'),(38,'Can change Consultation',11,'change_consultation'),(39,'Can delete Consultation',11,'delete_consultation'),(40,'Can view Consultation',11,'view_consultation'),(41,'Can add Prescription',14,'add_prescription'),(42,'Can change Prescription',14,'change_prescription'),(43,'Can delete Prescription',14,'delete_prescription'),(44,'Can view Prescription',14,'view_prescription'),(45,'Can add Prescription Item',15,'add_prescriptionitem'),(46,'Can change Prescription Item',15,'change_prescriptionitem'),(47,'Can delete Prescription Item',15,'delete_prescriptionitem'),(48,'Can view Prescription Item',15,'view_prescriptionitem'),(49,'Can add Triage',16,'add_triage'),(50,'Can change Triage',16,'change_triage'),(51,'Can delete Triage',16,'delete_triage'),(52,'Can view Triage',16,'view_triage'),(53,'Can add Common Diagnosis',10,'add_commondiagnosis'),(54,'Can change Common Diagnosis',10,'change_commondiagnosis'),(55,'Can delete Common Diagnosis',10,'delete_commondiagnosis'),(56,'Can view Common Diagnosis',10,'view_commondiagnosis'),(57,'Can add Follow-up Progress Entry',12,'add_followupprogress'),(58,'Can change Follow-up Progress Entry',12,'change_followupprogress'),(59,'Can delete Follow-up Progress Entry',12,'delete_followupprogress'),(60,'Can view Follow-up Progress Entry',12,'view_followupprogress'),(61,'Can add Follow-up Request',13,'add_followuprequest'),(62,'Can change Follow-up Request',13,'change_followuprequest'),(63,'Can delete Follow-up Request',13,'delete_followuprequest'),(64,'Can view Follow-up Request',13,'view_followuprequest'),(65,'Can add College',17,'add_college'),(66,'Can change College',17,'change_college'),(67,'Can delete College',17,'delete_college'),(68,'Can view College',17,'view_college'),(69,'Can add Course',18,'add_course'),(70,'Can change Course',18,'change_course'),(71,'Can delete Course',18,'delete_course'),(72,'Can view Course',18,'view_course'),(73,'Can add Medicine',19,'add_medicine'),(74,'Can change Medicine',19,'change_medicine'),(75,'Can delete Medicine',19,'delete_medicine'),(76,'Can view Medicine',19,'view_medicine'),(77,'Can add Stock Movement',20,'add_stockmovement'),(78,'Can change Stock Movement',20,'change_stockmovement'),(79,'Can delete Stock Movement',20,'delete_stockmovement'),(80,'Can view Stock Movement',20,'view_stockmovement'),(81,'Can add Medical Certificate',24,'add_medicalcertificate'),(82,'Can change Medical Certificate',24,'change_medicalcertificate'),(83,'Can delete Medical Certificate',24,'delete_medicalcertificate'),(84,'Can view Medical Certificate',24,'view_medicalcertificate'),(85,'Can add Certificate Audit Log',21,'add_certificateauditlog'),(86,'Can change Certificate Audit Log',21,'change_certificateauditlog'),(87,'Can delete Certificate Audit Log',21,'delete_certificateauditlog'),(88,'Can view Certificate Audit Log',21,'view_certificateauditlog'),(89,'Can add Certificate Template Text',23,'add_certificatetemplatetext'),(90,'Can change Certificate Template Text',23,'change_certificatetemplatetext'),(91,'Can delete Certificate Template Text',23,'delete_certificatetemplatetext'),(92,'Can view Certificate Template Text',23,'view_certificatetemplatetext'),(93,'Can add Certificate Template Change Log',22,'add_certificatetemplatechangelog'),(94,'Can change Certificate Template Change Log',22,'change_certificatetemplatechangelog'),(95,'Can delete Certificate Template Change Log',22,'delete_certificatetemplatechangelog'),(96,'Can view Certificate Template Change Log',22,'view_certificatetemplatechangelog'),(97,'Can add About Card',25,'add_aboutcard'),(98,'Can change About Card',25,'change_aboutcard'),(99,'Can delete About Card',25,'delete_aboutcard'),(100,'Can view About Card',25,'view_aboutcard'),(101,'Can add About Content',26,'add_aboutcontent'),(102,'Can change About Content',26,'change_aboutcontent'),(103,'Can delete About Content',26,'delete_aboutcontent'),(104,'Can view About Content',26,'view_aboutcontent'),(105,'Can add About Pill',27,'add_aboutpill'),(106,'Can change About Pill',27,'change_aboutpill'),(107,'Can delete About Pill',27,'delete_aboutpill'),(108,'Can view About Pill',27,'view_aboutpill'),(109,'Can add Contact Section Header',28,'add_contactcontent'),(110,'Can change Contact Section Header',28,'change_contactcontent'),(111,'Can delete Contact Section Header',28,'delete_contactcontent'),(112,'Can view Contact Section Header',28,'view_contactcontent'),(113,'Can add Contact Item',29,'add_contactitem'),(114,'Can change Contact Item',29,'change_contactitem'),(115,'Can delete Contact Item',29,'delete_contactitem'),(116,'Can view Contact Item',29,'view_contactitem'),(117,'Can add Feature Card',30,'add_featurecard'),(118,'Can change Feature Card',30,'change_featurecard'),(119,'Can delete Feature Card',30,'delete_featurecard'),(120,'Can view Feature Card',30,'view_featurecard'),(121,'Can add Features Section Header',31,'add_featurescontent'),(122,'Can change Features Section Header',31,'change_featurescontent'),(123,'Can delete Features Section Header',31,'delete_featurescontent'),(124,'Can view Features Section Header',31,'view_featurescontent'),(125,'Can add Hero Content',32,'add_herocontent'),(126,'Can change Hero Content',32,'change_herocontent'),(127,'Can delete Hero Content',32,'delete_herocontent'),(128,'Can view Hero Content',32,'view_herocontent'),(129,'Can add Hero Stat',33,'add_herostat'),(130,'Can change Hero Stat',33,'change_herostat'),(131,'Can delete Hero Stat',33,'delete_herostat'),(132,'Can view Hero Stat',33,'view_herostat'),(133,'Can add Site Settings',34,'add_sitesettings'),(134,'Can change Site Settings',34,'change_sitesettings'),(135,'Can delete Site Settings',34,'delete_sitesettings'),(136,'Can view Site Settings',34,'view_sitesettings'),(137,'Can add Stats Strip Item',35,'add_statstrip'),(138,'Can change Stats Strip Item',35,'change_statstrip'),(139,'Can delete Stats Strip Item',35,'delete_statstrip'),(140,'Can view Stats Strip Item',35,'view_statstrip'),(141,'Can add notification',36,'add_notification'),(142,'Can change notification',36,'change_notification'),(143,'Can delete notification',36,'delete_notification'),(144,'Can view notification',36,'view_notification'),(145,'Can add Consultation Feedback',37,'add_consultationfeedback'),(146,'Can change Consultation Feedback',37,'change_consultationfeedback'),(147,'Can delete Consultation Feedback',37,'delete_consultationfeedback'),(148,'Can view Consultation Feedback',37,'view_consultationfeedback'),(149,'Can add Audit Log',38,'add_auditlog'),(150,'Can change Audit Log',38,'change_auditlog'),(151,'Can delete Audit Log',38,'delete_auditlog'),(152,'Can view Audit Log',38,'view_auditlog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `certificates_certificateauditlog`
--

DROP TABLE IF EXISTS `certificates_certificateauditlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `certificates_certificateauditlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(20) NOT NULL,
  `details` longtext NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `certificate_id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_certifi_certificate_id_bb921b2f_fk_certifica` (`certificate_id`),
  KEY `certificates_certifi_user_id_34c30e6d_fk_accounts_` (`user_id`),
  KEY `certificates_certificateauditlog_action_3097828d` (`action`),
  CONSTRAINT `certificates_certifi_certificate_id_bb921b2f_fk_certifica` FOREIGN KEY (`certificate_id`) REFERENCES `certificates_medicalcertificate` (`id`),
  CONSTRAINT `certificates_certifi_user_id_34c30e6d_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `certificates_certificateauditlog`
--

LOCK TABLES `certificates_certificateauditlog` WRITE;
/*!40000 ALTER TABLE `certificates_certificateauditlog` DISABLE KEYS */;
INSERT INTO `certificates_certificateauditlog` VALUES (1,'created','Draft created (type: fit_to_work)','2026-07-17 05:50:31.460632',1,3),(2,'updated','Details saved','2026-07-17 05:50:58.329286',1,3),(3,'created','Draft created (type: standard)','2026-07-21 02:31:11.233696',2,3),(4,'updated','Details saved','2026-07-21 02:31:22.696610',2,3),(5,'created','Draft created (type: fit_to_work)','2026-07-21 02:31:47.981844',3,3),(6,'updated','Details saved','2026-07-21 02:32:09.275864',3,3),(7,'created','Draft created (type: fit_to_work)','2026-07-23 01:49:01.757207',16,3),(8,'updated','Details saved','2026-07-23 01:49:43.404054',16,3),(9,'issued','Certificate MC-2026-000001 issued','2026-07-23 01:50:25.797347',16,3),(10,'viewed','Viewed by BRADI CARCASONA','2026-07-23 01:50:25.876273',16,3),(11,'downloaded_docx','Downloaded .docx by BRADI CARCASONA','2026-07-23 01:50:39.841900',16,3),(12,'created','Draft created (type: fit_to_work)','2026-07-23 03:35:09.910909',17,3),(13,'created','Draft created (type: standard)','2026-07-23 03:46:14.169282',18,3),(14,'created','Draft created (type: ojt)','2026-07-23 04:51:13.201135',19,3),(15,'created','Draft created (type: absences)','2026-07-29 05:55:38.153827',20,3),(16,'updated','Details saved','2026-07-29 05:55:53.389635',20,3),(17,'issued','Certificate MC-2026-000002 issued','2026-07-29 05:56:18.505728',20,3),(18,'viewed','Viewed by BRADI CARCASONA','2026-07-29 05:56:18.785932',20,3),(19,'downloaded_docx','Downloaded .docx by BRADI CARCASONA','2026-07-29 05:56:29.982722',20,3),(20,'printed','Printed by BRADI CARCASONA','2026-07-29 05:57:19.588842',20,3),(21,'printed','Printed by BRADI CARCASONA','2026-07-29 05:58:19.951648',20,3),(22,'printed','Printed by BRADI CARCASONA','2026-07-29 05:59:19.930297',20,3),(23,'printed','Printed by BRADI CARCASONA','2026-07-29 06:00:20.087237',20,3),(24,'created','Draft created (type: absences)','2026-07-29 09:08:50.095123',21,3),(25,'updated','Details saved','2026-07-29 09:08:57.209146',21,3),(26,'updated','Details saved','2026-07-29 09:09:57.447291',21,3),(27,'issued','Certificate MC-2026-000003 issued','2026-07-29 09:10:07.342356',21,3),(28,'viewed','Viewed by BRADI CARCASONA','2026-07-29 09:10:07.392205',21,3),(29,'printed','Printed by BRADI CARCASONA','2026-07-29 09:11:07.556195',21,3),(30,'printed','Printed by BRADI CARCASONA','2026-07-29 09:12:08.537407',21,3),(31,'printed','Printed by BRADI CARCASONA','2026-07-29 09:13:08.525620',21,3),(32,'printed','Printed by BRADI CARCASONA','2026-07-29 09:14:08.527395',21,3),(33,'printed','Printed by BRADI CARCASONA','2026-07-29 09:15:08.522996',21,3),(34,'printed','Printed by BRADI CARCASONA','2026-07-29 09:16:08.538372',21,3),(35,'printed','Printed by BRADI CARCASONA','2026-07-29 09:17:49.576006',21,3),(36,'printed','Printed by BRADI CARCASONA','2026-07-29 09:18:07.558045',21,3),(37,'created','Draft created (type: absences)','2026-08-07 01:09:46.768867',22,3),(38,'updated','Details saved','2026-08-07 01:09:53.564360',22,3),(39,'voided','Discarded by user to start over','2026-08-07 01:10:30.944327',22,3),(40,'created','Draft created (type: ojt)','2026-08-07 01:17:34.851594',23,3),(41,'created','Draft created (type: ojt)','2026-08-11 09:54:32.237112',24,3),(42,'updated','Details saved','2026-08-11 09:54:52.527649',24,3),(43,'issued','Certificate MC-2026-000004 issued','2026-08-11 09:55:02.231134',24,3),(44,'viewed','Viewed by BRADI CARCASONA','2026-08-11 09:55:02.282925',24,3),(45,'downloaded_docx','Downloaded .docx by BRADI CARCASONA','2026-08-11 09:55:11.353114',24,3),(46,'printed','Printed by BRADI CARCASONA','2026-08-11 09:56:03.405780',24,3);
/*!40000 ALTER TABLE `certificates_certificateauditlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `certificates_certificatetemplatechangelog`
--

DROP TABLE IF EXISTS `certificates_certificatetemplatechangelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `certificates_certificatetemplatechangelog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `old_text` longtext NOT NULL,
  `new_text` longtext NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `slot_id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `certificates_certifi_slot_id_0cc85b17_fk_certifica` (`slot_id`),
  KEY `certificates_certifi_user_id_0713bc37_fk_accounts_` (`user_id`),
  CONSTRAINT `certificates_certifi_slot_id_0cc85b17_fk_certifica` FOREIGN KEY (`slot_id`) REFERENCES `certificates_certificatetemplatetext` (`id`),
  CONSTRAINT `certificates_certifi_user_id_0713bc37_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `certificates_certificatetemplatechangelog`
--

LOCK TABLES `certificates_certificatetemplatechangelog` WRITE;
/*!40000 ALTER TABLE `certificates_certificatetemplatechangelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `certificates_certificatetemplatechangelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `certificates_certificatetemplatetext`
--

DROP TABLE IF EXISTS `certificates_certificatetemplatetext`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `certificates_certificatetemplatetext` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `certificate_type` varchar(20) NOT NULL,
  `slot_key` varchar(50) NOT NULL,
  `text` longtext NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `updated_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificates_certificate_certificate_type_slot_ke_ca994b34_uniq` (`certificate_type`,`slot_key`),
  KEY `certificates_certifi_updated_by_id_8a396852_fk_accounts_` (`updated_by_id`),
  CONSTRAINT `certificates_certifi_updated_by_id_8a396852_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `certificates_certificatetemplatetext`
--

LOCK TABLES `certificates_certificatetemplatetext` WRITE;
/*!40000 ALTER TABLE `certificates_certificatetemplatetext` DISABLE KEYS */;
INSERT INTO `certificates_certificatetemplatetext` VALUES (12,'absences','body','This is to certify that {patient_name}, {age} years old and a {course} student in this campus, was examined and treated at this clinic on {exam_date}.\n\nDiagnosis:\n• {diagnosis}\n\nThe patient is advised to rest from {rest_from} to {rest_to}.\n\nRemarks:\n{remarks}\n\nGiven this {day} day of {month}, {year} at {place}, for whatever legal purpose it may serve.','2026-07-23 05:02:38.881688',NULL),(13,'ojt','body','This is to certify that {patient_name}, {age} years old and a {course} student in this campus, has been examined and found to be PHYSICALLY FIT to return to On-the-Job Training (OJT).\n\nAssessment: {work_assessment}\n\nFindings:\n• {diagnosis}\n\nRecommended Return Date: {return_date}\n\nRestrictions/Limitations:\n{restrictions}\n\nGiven this {day} day of {month}, {year} at {place}, for whatever legal purpose it may serve.\n\nRemarks:\n{remarks}','2026-07-23 05:02:38.897543',NULL),(14,'activities','body','This is to certify that {patient_name}, {age} years old and a {course} student in this campus, has been examined and found to be PHYSICALLY FIT to participate in:\n\n{activity_name}\n\nFitness Status: {fitness_status}\n\nFindings:\n• {diagnosis}\n\nGiven this {day} day of {month}, {year} at {place}, for whatever legal purpose it may serve.\n\nRemarks:\n{remarks}','2026-07-23 05:02:38.902882',NULL);
/*!40000 ALTER TABLE `certificates_certificatetemplatetext` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `certificates_medicalcertificate`
--

DROP TABLE IF EXISTS `certificates_medicalcertificate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `certificates_medicalcertificate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `diagnosis` longtext NOT NULL,
  `rest_from` date DEFAULT NULL,
  `rest_to` date DEFAULT NULL,
  `remarks` longtext NOT NULL,
  `issued_at` datetime(6) DEFAULT NULL,
  `consultation_id` bigint NOT NULL,
  `doctor_id` bigint DEFAULT NULL,
  `certificate_type` varchar(20) NOT NULL,
  `activity_name` varchar(200) NOT NULL,
  `certificate_number` varchar(20) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `diagnosis_snapshot` longtext NOT NULL,
  `fitness_status` varchar(20) NOT NULL,
  `patient_id` bigint DEFAULT NULL,
  `restrictions` longtext NOT NULL,
  `return_date` date DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `template_version` varchar(10) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `work_assessment` varchar(50) NOT NULL,
  `rendered_text_snapshot` json DEFAULT NULL,
  `place` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificate_number` (`certificate_number`),
  KEY `certificates_medical_doctor_id_7acd3ec1_fk_accounts_` (`doctor_id`),
  KEY `certificates_medical_patient_id_8d0d08d4_fk_patients_` (`patient_id`),
  KEY `certificates_medicalcertificate_consultation_id_20c1ba9b` (`consultation_id`),
  KEY `certificate_status_579324_idx` (`status`,`created_at` DESC),
  KEY `certificate_certifi_bba2bf_idx` (`certificate_number`),
  KEY `certificates_medicalcertificate_status_f2517b1b` (`status`),
  CONSTRAINT `certificates_medical_consultation_id_20c1ba9b_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `certificates_medical_doctor_id_7acd3ec1_fk_accounts_` FOREIGN KEY (`doctor_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `certificates_medical_patient_id_8d0d08d4_fk_patients_` FOREIGN KEY (`patient_id`) REFERENCES `patients_patient` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `certificates_medicalcertificate`
--

LOCK TABLES `certificates_medicalcertificate` WRITE;
/*!40000 ALTER TABLE `certificates_medicalcertificate` DISABLE KEYS */;
INSERT INTO `certificates_medicalcertificate` VALUES (1,'nahh',NULL,NULL,'ok',NULL,1,3,'ojt','',NULL,'2026-07-17 05:50:31.458237','','',2,'nah','2026-07-17','draft','3.0','2026-07-17 05:50:58.298643','fit_to_return',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(2,'nahh','2026-07-22','2026-07-25','oki',NULL,2,3,'absences','',NULL,'2026-07-21 02:31:11.230589','','',3,'',NULL,'draft','3.0','2026-07-21 02:31:22.679957','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(3,'nahh',NULL,NULL,'oks',NULL,2,3,'ojt','',NULL,'2026-07-21 02:31:47.979417','','',3,'aas','2026-07-21','draft','3.0','2026-07-21 02:32:09.264319','fit_to_return',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(16,'okss',NULL,NULL,'physically fit','2026-07-23 01:50:25.794205',7,3,'ojt','','MC-2026-000001','2026-07-23 01:49:01.753070','okss','',2,'nah','2026-07-24','issued','3.0','2026-07-23 01:49:43.396441','fit_to_return','\"This is to certify that BRADI CARCASONA, 21 years old, a Bachelor of Science in Information Technology student in this campus, was seen and examined through Medical/Physical Examination by the undersigned and is Physically Fit to undergo  on July 23, 2026 at Bawayan City.\\n\\nVital Signs:\\nTemp.: 36.00   BP: 120/80   PR: 72   RR: 16\\n\\nIssued this 23 day of July, 2026 at Bawayan City.\\n\\nRemarks:\\nphysically fit\"','Bawayan City'),(17,'healthy',NULL,NULL,'',NULL,8,3,'fit_to_work','',NULL,'2026-07-23 03:35:09.902206','','',2,'',NULL,'draft','3.0','2026-07-23 03:35:09.902233','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(18,'nah',NULL,NULL,'',NULL,9,3,'standard','',NULL,'2026-07-23 03:46:14.163947','','',2,'',NULL,'draft','3.0','2026-07-23 03:46:14.163964','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(19,'Healthy',NULL,NULL,'',NULL,10,3,'ojt','',NULL,'2026-07-23 04:51:13.181998','','',2,'',NULL,'draft','3.0','2026-07-23 04:51:13.182024','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(20,'alaws','2026-07-29','2026-07-30','alaws','2026-07-29 05:56:18.498832',11,3,'absences','','MC-2026-000002','2026-07-29 05:55:38.150060','alaws','',9,'',NULL,'issued','3.0','2026-07-29 05:55:53.381815','','\"This is to certify that Kristel May Baga-an, 22 years old and a Bachelor of Elementary Education student in this campus, was examined and treated at this clinic on July 29, 2026.\\n\\nDiagnosis:\\n• alaws\\n\\nThe patient is advised to rest from July 29, 2026 to July 30, 2026.\\n\\nRemarks:\\nalaws\\n\\nGiven this 29 day of July, 2026 at Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines, for whatever legal purpose it may serve.\"','Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(21,'okss',NULL,NULL,'nah','2026-07-29 09:10:07.336730',12,3,'absences','','MC-2026-000003','2026-07-29 09:08:50.091270','okss','',2,'',NULL,'issued','3.0','2026-07-29 09:09:57.430996','','\"This is to certify that BRADI CARCASONA, 21 years old and a  student in this campus, was examined and treated at this clinic on July 29, 2026.\\n\\nDiagnosis:\\n• okss\\n\\nThe patient is advised to rest from  to .\\n\\nRemarks:\\nnah\\n\\nGiven this 29 day of July, 2026 at Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines, for whatever legal purpose it may serve.\"','Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(22,'nah',NULL,NULL,'good',NULL,14,3,'absences','',NULL,'2026-08-07 01:09:46.753749','','',2,'',NULL,'voided','3.0','2026-08-07 01:09:53.553179','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(23,'nah',NULL,NULL,'',NULL,14,3,'ojt','',NULL,'2026-08-07 01:17:34.827566','','',2,'',NULL,'draft','3.0','2026-08-07 01:17:34.827682','',NULL,'Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines'),(24,'okss',NULL,NULL,'physically fit','2026-08-11 09:55:02.227886',16,3,'ojt','','MC-2026-000004','2026-08-11 09:54:32.229907','okss','',2,'',NULL,'issued','3.0','2026-08-11 09:54:52.520394','','\"This is to certify that Bradi Carcasona, 21 years old and a  student in this campus, has been examined and found to be PHYSICALLY FIT to return to On-the-Job Training (OJT).\\n\\nAssessment: \\n\\nFindings:\\n• okss\\n\\nRecommended Return Date: \\n\\nRestrictions/Limitations:\\n\\n\\nGiven this 11 day of August, 2026 at Bawayan City, for whatever legal purpose it may serve.\\n\\nRemarks:\\nphysically fit\"','Bawayan City');
/*!40000 ALTER TABLE `certificates_medicalcertificate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `colleges_college`
--

DROP TABLE IF EXISTS `colleges_college`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `colleges_college` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `abbreviation` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `abbreviation` (`abbreviation`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `colleges_college`
--

LOCK TABLES `colleges_college` WRITE;
/*!40000 ALTER TABLE `colleges_college` DISABLE KEYS */;
INSERT INTO `colleges_college` VALUES (1,'College of Arts and Sciences','CAS','2026-07-21 07:01:03.993069'),(2,'College of Business and Accountancy','CBA','2026-07-21 07:01:04.012658'),(3,'College of Criminal Justice Education','CCJE','2026-07-21 07:01:04.016430'),(4,'College of Teacher Education','CTED','2026-07-21 07:01:04.021011'),(5,'College of Agriculture and Forestry','CAF','2026-07-21 07:01:04.025022'),(6,'College of Industrial Technology','CIT','2026-07-21 07:01:04.028242');
/*!40000 ALTER TABLE `colleges_college` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `colleges_course`
--

DROP TABLE IF EXISTS `colleges_course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `colleges_course` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `college_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `colleges_course_name_college_id_58aff0d0_uniq` (`name`,`college_id`),
  KEY `colleges_course_college_id_911c9532_fk_colleges_college_id` (`college_id`),
  CONSTRAINT `colleges_course_college_id_911c9532_fk_colleges_college_id` FOREIGN KEY (`college_id`) REFERENCES `colleges_college` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `colleges_course`
--

LOCK TABLES `colleges_course` WRITE;
/*!40000 ALTER TABLE `colleges_course` DISABLE KEYS */;
INSERT INTO `colleges_course` VALUES (1,'Bachelor of Science in Information Technology','2026-07-21 07:01:04.041448',1),(2,'Bachelor of Science in Computer Science','2026-07-21 07:01:04.048919',1),(3,'Bachelor of Science in Human Resource Management','2026-07-21 07:01:04.054737',2),(4,'Bachelor of Science in Office Administration','2026-07-21 07:01:04.058025',2),(5,'Bachelor of Science in Business Administration','2026-07-21 07:01:04.061636',2),(6,'Bachelor of Science in Criminology','2026-07-21 07:01:04.065596',3),(7,'Bachelor of Secondary Education Major in Science','2026-07-21 07:01:04.070411',4),(8,'Bachelor of Secondary Education Major in Math','2026-07-21 07:01:04.074588',4),(9,'Bachelor of Secondary Education Major in English','2026-07-21 07:01:04.078807',4),(10,'Bachelor of Elementary Education','2026-07-21 07:01:04.081541',4),(11,'Bachelor of Science in Agronomy','2026-07-21 07:01:04.087735',5),(12,'Bachelor of Science in Forestry','2026-07-21 07:01:04.096957',5),(13,'Bachelor of Science in Animal Science','2026-07-21 07:01:04.112951',5),(14,'Bachelor of Science in Industrial Technology major in Computer Technology','2026-07-21 07:01:04.116889',6),(15,'Bachelor of Science in Industrial Technology major in Automotive','2026-07-21 07:01:04.120791',6),(16,'Bachelor of Science in Industrial Technology major in Electronics','2026-07-21 07:01:04.124257',6);
/*!40000 ALTER TABLE `colleges_course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_commondiagnosis`
--

DROP TABLE IF EXISTS `consultations_commondiagnosis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_commondiagnosis` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `category` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_commondiagnosis`
--

LOCK TABLES `consultations_commondiagnosis` WRITE;
/*!40000 ALTER TABLE `consultations_commondiagnosis` DISABLE KEYS */;
/*!40000 ALTER TABLE `consultations_commondiagnosis` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_consultation`
--

DROP TABLE IF EXISTS `consultations_consultation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_consultation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` varchar(20) NOT NULL,
  `symptoms` longtext NOT NULL,
  `medical_history` longtext NOT NULL,
  `severity_description` longtext NOT NULL,
  `additional_notes` longtext NOT NULL,
  `queue_number` int unsigned DEFAULT NULL,
  `scheduled_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `patient_id` bigint NOT NULL,
  `closed_at` datetime(6) DEFAULT NULL,
  `closure_notes` longtext NOT NULL,
  `follow_up_count` int unsigned NOT NULL,
  `is_original_case` tinyint(1) NOT NULL,
  `last_follow_up_date` datetime(6) DEFAULT NULL,
  `parent_consultation_id` bigint DEFAULT NULL,
  `recommended_follow_up_date` date DEFAULT NULL,
  `chief_complaint` longtext NOT NULL,
  `active_flag` int GENERATED ALWAYS AS ((case when (`status` in (_utf8mb4'pending',_utf8mb4'queued',_utf8mb4'scheduled',_utf8mb4'triaged',_utf8mb4'active_follow_up')) then 1 else NULL end)) STORED,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_active_consultation_per_patient_mysql` (`patient_id`,`active_flag`),
  KEY `consultatio_status_49d4ed_idx` (`status`,`created_at` DESC),
  KEY `consultatio_patient_1ac522_idx` (`patient_id`,`created_at` DESC),
  KEY `consultations_consultation_status_467f65b4` (`status`),
  KEY `consultations_consul_parent_consultation__11e6538b_fk_consultat` (`parent_consultation_id`),
  CONSTRAINT `consultations_consul_parent_consultation__11e6538b_fk_consultat` FOREIGN KEY (`parent_consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `consultations_consul_patient_id_6a939c5c_fk_patients_` FOREIGN KEY (`patient_id`) REFERENCES `patients_patient` (`id`),
  CONSTRAINT `consultations_consultation_chk_1` CHECK ((`queue_number` >= 0)),
  CONSTRAINT `consultations_consultation_chk_2` CHECK ((`follow_up_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_consultation`
--

LOCK TABLES `consultations_consultation` WRITE;
/*!40000 ALTER TABLE `consultations_consultation` DISABLE KEYS */;
INSERT INTO `consultations_consultation` (`id`, `status`, `symptoms`, `medical_history`, `severity_description`, `additional_notes`, `queue_number`, `scheduled_at`, `created_at`, `updated_at`, `patient_id`, `closed_at`, `closure_notes`, `follow_up_count`, `is_original_case`, `last_follow_up_date`, `parent_consultation_id`, `recommended_follow_up_date`, `chief_complaint`) VALUES (1,'completed','nah','ajaja','aaa','okk',1,NULL,'2026-07-17 05:45:50.989923','2026-07-17 05:46:10.446913',2,NULL,'',0,1,NULL,NULL,NULL,''),(2,'active_follow_up','nah','ahah','aah','hah',1,NULL,'2026-07-21 02:29:32.489192','2026-07-21 02:29:59.219265',3,NULL,'',0,1,NULL,NULL,'2026-07-22',''),(7,'completed','hi po','anann','ok','ss',1,NULL,'2026-07-23 01:46:52.411834','2026-07-23 01:47:16.100528',2,NULL,'',0,1,NULL,NULL,NULL,''),(8,'completed','micho gay','bading','severe','ok ra',2,NULL,'2026-07-23 03:33:22.837369','2026-07-23 03:33:49.975156',2,NULL,'',0,1,NULL,NULL,NULL,''),(9,'completed','ok','akaak','aksk','cck',3,NULL,'2026-07-23 03:44:27.219034','2026-07-23 03:44:55.801145',2,NULL,'',0,1,NULL,NULL,NULL,''),(10,'completed','nah','nah','oks ra','nah',4,NULL,'2026-07-23 04:31:39.712109','2026-07-23 04:32:07.047214',2,NULL,'',0,1,NULL,NULL,NULL,''),(11,'completed','sakit akoa bulsa kag wala ko kwarta','','headache','',1,NULL,'2026-07-29 05:52:25.513371','2026-07-29 05:53:38.409573',9,NULL,'',0,1,NULL,NULL,NULL,''),(12,'completed','secret','oks','nahh','oki',2,NULL,'2026-07-29 09:07:23.595010','2026-07-29 09:07:52.692833',2,NULL,'',0,1,NULL,NULL,NULL,''),(13,'completed','sample','','Sample','',1,NULL,'2026-07-30 06:44:01.045169','2026-07-30 06:44:54.247306',2,NULL,'',0,1,NULL,NULL,NULL,'sampleeee'),(14,'completed','nah','ss','aa','snn',1,NULL,'2026-08-06 05:29:14.131941','2026-08-06 05:29:36.313417',2,NULL,'',0,1,NULL,NULL,NULL,'nahh'),(15,'completed','idk','okss','nah','',2,NULL,'2026-08-06 06:11:41.338664','2026-08-06 06:12:06.317445',2,NULL,'',0,1,NULL,NULL,NULL,'idkkkk'),(16,'completed','sample','','mild','',1,NULL,'2026-08-07 02:07:12.932902','2026-08-07 02:07:32.576417',2,NULL,'',0,1,NULL,NULL,NULL,'sample only');
/*!40000 ALTER TABLE `consultations_consultation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_followupprogress`
--

DROP TABLE IF EXISTS `consultations_followupprogress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_followupprogress` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `visit_number` int unsigned NOT NULL,
  `symptoms` longtext NOT NULL,
  `assessment` longtext NOT NULL,
  `treatment_notes` longtext NOT NULL,
  `recommendations` longtext NOT NULL,
  `notes` longtext NOT NULL,
  `follow_up_status` varchar(20) NOT NULL,
  `requires_follow_up` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `consultation_id` bigint NOT NULL,
  `doctor_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `consultations_followuppr_consultation_id_visit_nu_037fc7c7_uniq` (`consultation_id`,`visit_number`),
  KEY `consultatio_consult_f7b792_idx` (`consultation_id`,`visit_number` DESC),
  KEY `consultatio_follow__1bf8c8_idx` (`follow_up_status`,`created_at` DESC),
  KEY `consultations_follow_doctor_id_7964d442_fk_accounts_` (`doctor_id`),
  KEY `consultations_followupprogress_follow_up_status_0d0ebfae` (`follow_up_status`),
  CONSTRAINT `consultations_follow_consultation_id_f7839d61_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `consultations_follow_doctor_id_7964d442_fk_accounts_` FOREIGN KEY (`doctor_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `consultations_followupprogress_chk_1` CHECK ((`visit_number` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_followupprogress`
--

LOCK TABLES `consultations_followupprogress` WRITE;
/*!40000 ALTER TABLE `consultations_followupprogress` DISABLE KEYS */;
/*!40000 ALTER TABLE `consultations_followupprogress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_followuprequest`
--

DROP TABLE IF EXISTS `consultations_followuprequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_followuprequest` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `request_status` varchar(20) NOT NULL,
  `queue_number` int unsigned DEFAULT NULL,
  `scheduled_at` datetime(6) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `consultation_id` bigint NOT NULL,
  `patient_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `consultations_follow_patient_id_30b87f5f_fk_patients_` (`patient_id`),
  KEY `consultations_followuprequest_request_status_c9ab2c1b` (`request_status`),
  KEY `consultatio_request_2fd086_idx` (`request_status`,`created_at` DESC),
  KEY `consultatio_consult_09aa9d_idx` (`consultation_id`,`created_at` DESC),
  CONSTRAINT `consultations_follow_consultation_id_1f4bb5ce_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `consultations_follow_patient_id_30b87f5f_fk_patients_` FOREIGN KEY (`patient_id`) REFERENCES `patients_patient` (`id`),
  CONSTRAINT `consultations_followuprequest_chk_1` CHECK ((`queue_number` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_followuprequest`
--

LOCK TABLES `consultations_followuprequest` WRITE;
/*!40000 ALTER TABLE `consultations_followuprequest` DISABLE KEYS */;
/*!40000 ALTER TABLE `consultations_followuprequest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_prescription`
--

DROP TABLE IF EXISTS `consultations_prescription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_prescription` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `diagnosis` longtext NOT NULL,
  `treatment_plan` longtext NOT NULL,
  `prescribed_at` datetime(6) NOT NULL,
  `consultation_id` bigint NOT NULL,
  `doctor_id` bigint DEFAULT NULL,
  `follow_up_progress_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `consultations_prescr_doctor_id_b074e124_fk_accounts_` (`doctor_id`),
  KEY `consultations_prescription_consultation_id_06783661` (`consultation_id`),
  KEY `consultations_prescr_follow_up_progress_i_27e26d05_fk_consultat` (`follow_up_progress_id`),
  CONSTRAINT `consultations_prescr_consultation_id_06783661_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `consultations_prescr_doctor_id_b074e124_fk_accounts_` FOREIGN KEY (`doctor_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `consultations_prescr_follow_up_progress_i_27e26d05_fk_consultat` FOREIGN KEY (`follow_up_progress_id`) REFERENCES `consultations_followupprogress` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_prescription`
--

LOCK TABLES `consultations_prescription` WRITE;
/*!40000 ALTER TABLE `consultations_prescription` DISABLE KEYS */;
INSERT INTO `consultations_prescription` VALUES (1,'nahh','','2026-07-17 05:50:17.720093',1,3,NULL),(2,'nahh','oki','2026-07-21 02:30:59.393198',2,3,NULL),(7,'okss','','2026-07-23 01:47:57.891871',7,3,NULL),(8,'healthy','','2026-07-23 03:34:52.858417',8,3,NULL),(9,'nah','','2026-07-23 03:45:52.804710',9,3,NULL),(10,'Healthy','','2026-07-23 04:32:53.659223',10,3,NULL),(11,'alaws','alaws','2026-07-29 05:55:02.820444',11,3,NULL),(12,'okss','nah','2026-07-29 09:08:43.005835',12,3,NULL),(13,'nah','aah','2026-08-06 06:09:29.208893',13,3,NULL),(14,'nah','oks ra','2026-08-07 01:09:34.180624',14,3,NULL),(15,'oks na','alaws lang','2026-08-07 01:32:57.484376',15,3,NULL),(16,'okss','nah','2026-08-07 02:10:12.180327',16,3,NULL);
/*!40000 ALTER TABLE `consultations_prescription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_prescriptionitem`
--

DROP TABLE IF EXISTS `consultations_prescriptionitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_prescriptionitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned DEFAULT NULL,
  `instructions` varchar(200) NOT NULL,
  `medicine_id` bigint DEFAULT NULL,
  `prescription_id` bigint NOT NULL,
  `dosage` varchar(100) NOT NULL,
  `duration` varchar(100) NOT NULL,
  `frequency` varchar(100) NOT NULL,
  `medicine_name` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `consultations_prescr_prescription_id_ad06b8fb_fk_consultat` (`prescription_id`),
  KEY `consultations_prescr_medicine_id_6f67667a_fk_inventory` (`medicine_id`),
  CONSTRAINT `consultations_prescr_medicine_id_6f67667a_fk_inventory` FOREIGN KEY (`medicine_id`) REFERENCES `inventory_medicine` (`id`),
  CONSTRAINT `consultations_prescr_prescription_id_ad06b8fb_fk_consultat` FOREIGN KEY (`prescription_id`) REFERENCES `consultations_prescription` (`id`),
  CONSTRAINT `consultations_prescriptionitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_prescriptionitem`
--

LOCK TABLES `consultations_prescriptionitem` WRITE;
/*!40000 ALTER TABLE `consultations_prescriptionitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `consultations_prescriptionitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultations_triage`
--

DROP TABLE IF EXISTS `consultations_triage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultations_triage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `blood_pressure` varchar(20) NOT NULL,
  `temperature` decimal(5,2) NOT NULL,
  `pulse_rate` int unsigned NOT NULL,
  `urgency` varchar(10) NOT NULL,
  `notes` longtext NOT NULL,
  `triaged_at` datetime(6) NOT NULL,
  `consultation_id` bigint NOT NULL,
  `oxygen_saturation` decimal(5,2) DEFAULT NULL,
  `respiratory_rate` int unsigned DEFAULT NULL,
  `weight` decimal(5,2) DEFAULT NULL,
  `follow_up_progress_id` bigint DEFAULT NULL,
  `triaged_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `consultations_triage_consultation_id_c06e5ebc` (`consultation_id`),
  KEY `consultations_triage_follow_up_progress_i_283c822c_fk_consultat` (`follow_up_progress_id`),
  KEY `consultations_triage_triaged_by_id_dabfb967_fk_accounts_user_id` (`triaged_by_id`),
  CONSTRAINT `consultations_triage_consultation_id_c06e5ebc_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `consultations_triage_follow_up_progress_i_283c822c_fk_consultat` FOREIGN KEY (`follow_up_progress_id`) REFERENCES `consultations_followupprogress` (`id`),
  CONSTRAINT `consultations_triage_triaged_by_id_dabfb967_fk_accounts_user_id` FOREIGN KEY (`triaged_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `consultations_triage_chk_1` CHECK ((`pulse_rate` >= 0)),
  CONSTRAINT `consultations_triage_chk_2` CHECK ((`respiratory_rate` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultations_triage`
--

LOCK TABLES `consultations_triage` WRITE;
/*!40000 ALTER TABLE `consultations_triage` DISABLE KEYS */;
INSERT INTO `consultations_triage` VALUES (1,'120/80',36.00,72,'low','','2026-07-17 05:50:01.388380',1,NULL,NULL,NULL,NULL,3),(2,'120/80',36.00,71,'medium','asss\n\n[Amended by doctorr: n ahh]','2026-07-21 02:30:37.880178',2,98.00,15,NULL,NULL,3),(7,'120/80',36.00,72,'medium','','2026-07-23 01:47:50.461452',7,98.00,16,12.00,NULL,3),(8,'120/80',35.00,72,'medium','okay ra','2026-07-23 03:34:39.463852',8,94.00,16,45.00,NULL,3),(9,'120/80',36.00,71,'medium','nah','2026-07-23 03:45:42.117729',9,97.00,16,56.00,NULL,3),(10,'120/80',36.00,71,'medium','','2026-07-23 04:32:42.903865',10,92.00,15,56.00,NULL,3),(11,'120/80',36.00,72,'medium','','2026-07-29 05:54:33.434650',11,12.00,12,NULL,NULL,3),(12,'120/80',36.00,72,'medium','','2026-07-29 09:08:32.223830',12,98.00,16,56.00,NULL,3),(13,'120/80',36.50,72,'low','ala lang\n\n[Amended by doctorr: wrong value]','2026-08-06 05:30:33.766737',14,98.00,16,46.00,NULL,3),(14,'120/80',36.00,72,'low','','2026-08-06 06:08:15.512891',13,98.00,16,64.00,NULL,3),(15,'120/80',36.00,71,'medium','','2026-08-06 06:12:42.677209',15,98.00,16,NULL,NULL,3),(16,'120/80',36.00,72,'low','','2026-08-07 02:08:33.339954',16,98.00,16,56.00,NULL,3);
/*!40000 ALTER TABLE `consultations_triage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_aboutcard`
--

DROP TABLE IF EXISTS `core_aboutcard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_aboutcard` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(80) NOT NULL,
  `subtitle` varchar(120) NOT NULL,
  `icon` varchar(60) NOT NULL,
  `icon_color` varchar(30) NOT NULL,
  `order` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_aboutcard_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_aboutcard`
--

LOCK TABLES `core_aboutcard` WRITE;
/*!40000 ALTER TABLE `core_aboutcard` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_aboutcard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_aboutcontent`
--

DROP TABLE IF EXISTS `core_aboutcontent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_aboutcontent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `badge_text` varchar(80) NOT NULL,
  `headline` varchar(140) NOT NULL,
  `description_1` longtext NOT NULL,
  `description_2` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_aboutcontent`
--

LOCK TABLES `core_aboutcontent` WRITE;
/*!40000 ALTER TABLE `core_aboutcontent` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_aboutcontent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_aboutpill`
--

DROP TABLE IF EXISTS `core_aboutpill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_aboutpill` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `label` varchar(60) NOT NULL,
  `icon` varchar(60) NOT NULL,
  `order` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_aboutpill_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_aboutpill`
--

LOCK TABLES `core_aboutpill` WRITE;
/*!40000 ALTER TABLE `core_aboutpill` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_aboutpill` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_contactcontent`
--

DROP TABLE IF EXISTS `core_contactcontent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_contactcontent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `badge_text` varchar(80) NOT NULL,
  `headline` varchar(140) NOT NULL,
  `subtext` varchar(220) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_contactcontent`
--

LOCK TABLES `core_contactcontent` WRITE;
/*!40000 ALTER TABLE `core_contactcontent` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_contactcontent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_contactitem`
--

DROP TABLE IF EXISTS `core_contactitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_contactitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(80) NOT NULL,
  `detail` longtext NOT NULL,
  `icon` varchar(60) NOT NULL,
  `icon_bg` varchar(30) NOT NULL,
  `icon_color` varchar(30) NOT NULL,
  `order` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_contactitem_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_contactitem`
--

LOCK TABLES `core_contactitem` WRITE;
/*!40000 ALTER TABLE `core_contactitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_contactitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_featurecard`
--

DROP TABLE IF EXISTS `core_featurecard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_featurecard` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(80) NOT NULL,
  `description` longtext NOT NULL,
  `tag` varchar(40) NOT NULL,
  `icon` varchar(60) NOT NULL,
  `icon_bg` varchar(30) NOT NULL,
  `icon_color` varchar(30) NOT NULL,
  `order` smallint unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_featurecard_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_featurecard`
--

LOCK TABLES `core_featurecard` WRITE;
/*!40000 ALTER TABLE `core_featurecard` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_featurecard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_featurescontent`
--

DROP TABLE IF EXISTS `core_featurescontent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_featurescontent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `badge_text` varchar(80) NOT NULL,
  `headline` varchar(140) NOT NULL,
  `subtext` varchar(220) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_featurescontent`
--

LOCK TABLES `core_featurescontent` WRITE;
/*!40000 ALTER TABLE `core_featurescontent` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_featurescontent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_herocontent`
--

DROP TABLE IF EXISTS `core_herocontent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_herocontent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `badge_text` varchar(120) NOT NULL,
  `headline_plain` varchar(120) NOT NULL,
  `headline_accent` varchar(120) NOT NULL,
  `description` longtext NOT NULL,
  `cta_primary_label` varchar(60) NOT NULL,
  `cta_secondary_label` varchar(60) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_herocontent`
--

LOCK TABLES `core_herocontent` WRITE;
/*!40000 ALTER TABLE `core_herocontent` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_herocontent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_herostat`
--

DROP TABLE IF EXISTS `core_herostat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_herostat` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `value` varchar(20) NOT NULL,
  `label` varchar(60) NOT NULL,
  `order` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_herostat_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_herostat`
--

LOCK TABLES `core_herostat` WRITE;
/*!40000 ALTER TABLE `core_herostat` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_herostat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_sitesettings`
--

DROP TABLE IF EXISTS `core_sitesettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_sitesettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `site_name` varchar(100) NOT NULL,
  `site_title` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_sitesettings`
--

LOCK TABLES `core_sitesettings` WRITE;
/*!40000 ALTER TABLE `core_sitesettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_sitesettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_statstrip`
--

DROP TABLE IF EXISTS `core_statstrip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_statstrip` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `value` varchar(20) NOT NULL,
  `label` varchar(60) NOT NULL,
  `order` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `core_statstrip_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_statstrip`
--

LOCK TABLES `core_statstrip` WRITE;
/*!40000 ALTER TABLE `core_statstrip` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_statstrip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-07-17 05:44:31.571997','2','Sample User (patient)',3,'',6,1),(2,'2026-08-07 01:27:20.561791','7','CON — College of Nursing',3,'',17,13);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (6,'accounts','user'),(1,'admin','logentry'),(38,'audit_logs','auditlog'),(2,'auth','group'),(3,'auth','permission'),(21,'certificates','certificateauditlog'),(22,'certificates','certificatetemplatechangelog'),(23,'certificates','certificatetemplatetext'),(24,'certificates','medicalcertificate'),(17,'colleges','college'),(18,'colleges','course'),(10,'consultations','commondiagnosis'),(11,'consultations','consultation'),(12,'consultations','followupprogress'),(13,'consultations','followuprequest'),(14,'consultations','prescription'),(15,'consultations','prescriptionitem'),(16,'consultations','triage'),(4,'contenttypes','contenttype'),(25,'core','aboutcard'),(26,'core','aboutcontent'),(27,'core','aboutpill'),(28,'core','contactcontent'),(29,'core','contactitem'),(30,'core','featurecard'),(31,'core','featurescontent'),(32,'core','herocontent'),(33,'core','herostat'),(34,'core','sitesettings'),(35,'core','statstrip'),(37,'feedback','consultationfeedback'),(19,'inventory','medicine'),(20,'inventory','stockmovement'),(36,'notifications','notification'),(7,'patients','academicyearsettings'),(8,'patients','patient'),(9,'patients','patientprofile'),(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-07-17 03:38:10.910442'),(2,'contenttypes','0002_remove_content_type_name','2026-07-17 03:38:11.086103'),(3,'auth','0001_initial','2026-07-17 03:38:11.445154'),(4,'auth','0002_alter_permission_name_max_length','2026-07-17 03:38:11.514339'),(5,'auth','0003_alter_user_email_max_length','2026-07-17 03:38:11.523576'),(6,'auth','0004_alter_user_username_opts','2026-07-17 03:38:11.533647'),(7,'auth','0005_alter_user_last_login_null','2026-07-17 03:38:11.547577'),(8,'auth','0006_require_contenttypes_0002','2026-07-17 03:38:11.551340'),(9,'auth','0007_alter_validators_add_error_messages','2026-07-17 03:38:11.565138'),(10,'auth','0008_alter_user_username_max_length','2026-07-17 03:38:11.583153'),(11,'auth','0009_alter_user_last_name_max_length','2026-07-17 03:38:11.602463'),(12,'auth','0010_alter_group_name_max_length','2026-07-17 03:38:11.637421'),(13,'auth','0011_update_proxy_permissions','2026-07-17 03:38:11.651495'),(14,'auth','0012_alter_user_first_name_max_length','2026-07-17 03:38:11.665084'),(15,'accounts','0001_initial','2026-07-17 03:38:12.113854'),(16,'accounts','0002_studentprofile_alter_user_options_and_more','2026-07-17 03:38:12.318066'),(17,'accounts','0003_studentprofile_middle_name','2026-07-17 03:38:12.407570'),(18,'accounts','0004_user_force_password_change','2026-07-17 03:38:12.502186'),(19,'accounts','0005_alter_user_role','2026-07-17 03:38:12.514462'),(20,'accounts','0006_alter_user_options_alter_user_role_and_more','2026-07-17 03:38:12.566903'),(21,'accounts','0007_alter_user_options_alter_user_role','2026-07-17 03:38:12.589626'),(22,'accounts','0008_user_failed_login_attempts_user_locked_until_and_more','2026-07-17 03:38:13.086620'),(23,'accounts','0009_rename_reset_token_expiry_user_reset_otp_expiry_and_more','2026-07-17 03:38:13.315966'),(24,'accounts','0010_alter_user_role','2026-07-17 03:38:13.355847'),(25,'accounts','0011_alter_user_role','2026-07-17 03:38:13.399385'),(26,'accounts','0012_user_profile_picture','2026-07-17 03:38:13.528191'),(27,'accounts','0013_alter_user_reset_otp','2026-07-17 03:38:13.646256'),(28,'accounts','0014_alter_user_email','2026-07-17 03:38:13.764761'),(29,'accounts','0015_alter_user_email','2026-07-17 03:38:13.786553'),(30,'admin','0001_initial','2026-07-17 03:38:14.051615'),(31,'admin','0002_logentry_remove_auto_add','2026-07-17 03:38:14.065234'),(32,'admin','0003_logentry_add_action_flag_choices','2026-07-17 03:38:14.079470'),(33,'audit_logs','0001_initial','2026-07-17 03:38:14.407061'),(34,'audit_logs','0002_rename_audit_log_timestamp_idx_audit_logs__timesta_63825c_idx_and_more','2026-07-17 03:38:14.581097'),(35,'audit_logs','0003_remove_dental_certificates_module','2026-07-17 03:38:14.608713'),(36,'audit_logs','0004_alter_auditlog_module','2026-07-17 03:38:14.626850'),(37,'colleges','0001_initial','2026-07-17 03:38:14.713744'),(38,'patients','0001_initial','2026-07-17 03:38:15.209791'),(39,'patients','0002_patient_email_patient_emergency_contact_name_and_more','2026-07-17 03:38:15.633592'),(40,'patients','0003_patient_has_logged_in_patientprofile_address_and_more','2026-07-17 03:38:16.074093'),(41,'patients','0004_patientprofile_arthritis_patientprofile_asthma_and_more','2026-07-17 03:38:17.329721'),(42,'patients','0005_patient_profile_picture','2026-07-17 03:38:17.403858'),(43,'patients','0006_academicyearsettings_patient_archived_at_and_more','2026-07-17 03:38:17.870398'),(44,'inventory','0001_initial','2026-07-17 03:38:18.073513'),(45,'consultations','0001_initial','2026-07-17 03:38:18.666816'),(46,'consultations','0002_alter_consultation_patient_and_more','2026-07-17 03:38:18.932617'),(47,'consultations','0003_prescriptionitem_dosage_prescriptionitem_duration_and_more','2026-07-17 03:38:19.648464'),(48,'consultations','0004_triage_oxygen_saturation_triage_respiratory_rate_and_more','2026-07-17 03:38:19.870794'),(49,'certificates','0001_initial','2026-07-17 03:38:20.102805'),(50,'certificates','0002_medicalcertificate_certificate_type_and_more','2026-07-17 03:38:20.363444'),(51,'certificates','0003_medicalcertificate_status_and_more','2026-07-17 03:38:22.154109'),(52,'certificates','0004_rename_certificate_status_created_idx_certificate_status_579324_idx_and_more','2026-07-17 03:38:22.246243'),(53,'certificates','0005_certificatetemplatetext_certificatetemplatechangelog_and_more','2026-07-17 03:38:22.653733'),(54,'certificates','0006_seed_certificate_template_text','2026-07-17 03:38:22.693731'),(55,'certificates','0007_seed_closing_statement','2026-07-17 03:38:22.747283'),(56,'certificates','0008_consolidate_template_text_into_body','2026-07-17 03:38:22.846118'),(57,'certificates','0009_alter_medicalcertificate_rendered_text_snapshot_and_more','2026-07-17 03:38:22.967951'),(58,'certificates','0010_alter_certificatetemplatetext_certificate_type_and_more','2026-07-17 03:38:23.016172'),(59,'certificates','0011_alter_certificatetemplatetext_certificate_type_and_more','2026-07-17 03:38:23.070585'),(60,'certificates','0012_remove_dental_certificate_type','2026-07-17 03:38:23.113412'),(61,'colleges','0002_course','2026-07-17 03:38:23.344625'),(62,'colleges','0003_seed_courses','2026-07-17 03:38:23.465332'),(63,'consultations','0005_commondiagnosis','2026-07-17 03:38:23.542262'),(64,'consultations','0006_consultation_closed_at_consultation_closure_notes_and_more','2026-07-17 03:38:25.425961'),(65,'consultations','0007_consultation_recommended_follow_up_date','2026-07-17 03:38:25.570701'),(66,'consultations','0008_followuprequest','2026-07-17 03:38:25.799929'),(67,'consultations','0009_remove_triage_nurse_triage_triaged_by','2026-07-17 03:38:26.081447'),(68,'core','0001_initial','2026-07-17 03:38:26.438459'),(69,'feedback','0001_initial','2026-07-17 03:38:26.651695'),(70,'notifications','0001_initial','2026-07-17 03:38:26.919844'),(71,'notifications','0002_alter_notification_recipient_role','2026-07-17 03:38:26.961377'),(72,'patients','0007_patient_course','2026-07-17 03:38:27.131566'),(73,'patients','0008_patient_temp_password','2026-07-17 03:38:27.263083'),(74,'sessions','0001_initial','2026-07-17 03:38:27.322387'),(75,'accounts','0016_user_temp_password','2026-07-17 05:26:47.749014'),(76,'accounts','0017_fix_empty_email_to_null','2026-07-17 05:37:27.387481'),(77,'colleges','0004_seed_colleges_and_courses','2026-07-21 07:01:04.135732'),(78,'certificates','0013_add_place_field','2026-07-22 01:20:56.642041'),(79,'certificates','0014_update_template_text_body','2026-07-22 01:20:56.698224'),(80,'certificates','0015_rename_certificate_type_codes','2026-07-23 03:32:23.798833'),(81,'certificates','0016_fix_template_body_texts','2026-07-23 05:02:38.920903'),(82,'consultations','0010_consultation_chief_complaint','2026-08-06 05:34:42.552187'),(83,'consultations','0011_consultation_unique_active_consultation_per_patient','2026-08-07 01:50:35.924808'),(84,'consultations','0012_consultation_active_flag_and_more','2026-08-07 01:57:25.907220');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedback_consultationfeedback`
--

DROP TABLE IF EXISTS `feedback_consultationfeedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedback_consultationfeedback` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rating` smallint unsigned NOT NULL,
  `comment` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `consultation_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `consultation_id` (`consultation_id`),
  CONSTRAINT `feedback_consultatio_consultation_id_7ea9cedd_fk_consultat` FOREIGN KEY (`consultation_id`) REFERENCES `consultations_consultation` (`id`),
  CONSTRAINT `feedback_consultationfeedback_chk_1` CHECK ((`rating` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedback_consultationfeedback`
--

LOCK TABLES `feedback_consultationfeedback` WRITE;
/*!40000 ALTER TABLE `feedback_consultationfeedback` DISABLE KEYS */;
INSERT INTO `feedback_consultationfeedback` VALUES (1,5,'','2026-07-21 07:13:29.488048',1),(2,5,'okay ra','2026-07-23 01:51:38.438412',7),(3,5,'','2026-07-23 03:44:15.707089',8),(4,5,'oks','2026-07-23 04:31:24.123153',9),(5,5,'','2026-07-28 01:44:01.021361',10),(6,5,'','2026-07-29 06:00:23.443257',11),(7,5,'','2026-07-29 09:48:35.567454',12),(8,5,'','2026-08-06 06:10:28.526302',13),(9,5,'','2026-08-07 01:18:16.582924',14),(10,5,'','2026-08-07 02:06:55.913911',15);
/*!40000 ALTER TABLE `feedback_consultationfeedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_medicine`
--

DROP TABLE IF EXISTS `inventory_medicine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_medicine` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `generic_name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `quantity` int unsigned NOT NULL,
  `unit` varchar(20) NOT NULL,
  `low_stock_threshold` int unsigned NOT NULL,
  `batch_number` varchar(100) NOT NULL,
  `expiry_date` date DEFAULT NULL,
  `supplier` varchar(200) NOT NULL,
  `cost_per_unit` decimal(10,2) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `inventory_m_name_7f2fd2_idx` (`name`),
  KEY `inventory_m_quantit_3cd49e_idx` (`quantity`),
  CONSTRAINT `inventory_medicine_chk_1` CHECK ((`quantity` >= 0)),
  CONSTRAINT `inventory_medicine_chk_2` CHECK ((`low_stock_threshold` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_medicine`
--

LOCK TABLES `inventory_medicine` WRITE;
/*!40000 ALTER TABLE `inventory_medicine` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventory_medicine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_stockmovement`
--

DROP TABLE IF EXISTS `inventory_stockmovement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_stockmovement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `movement_type` varchar(20) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `reason` varchar(200) NOT NULL,
  `reference` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by` varchar(100) NOT NULL,
  `medicine_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `inventory_s_medicin_398238_idx` (`medicine_id`,`created_at` DESC),
  CONSTRAINT `inventory_stockmovem_medicine_id_f437fbbd_fk_inventory` FOREIGN KEY (`medicine_id`) REFERENCES `inventory_medicine` (`id`),
  CONSTRAINT `inventory_stockmovement_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_stockmovement`
--

LOCK TABLES `inventory_stockmovement` WRITE;
/*!40000 ALTER TABLE `inventory_stockmovement` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventory_stockmovement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications_notification`
--

DROP TABLE IF EXISTS `notifications_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `recipient_role` varchar(20) DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `message` longtext NOT NULL,
  `link` varchar(300) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `recipient_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `notificatio_recipie_a972ce_idx` (`recipient_id`,`created_at` DESC),
  KEY `notificatio_recipie_1d360f_idx` (`recipient_role`,`created_at` DESC),
  KEY `notificatio_is_read_9edb86_idx` (`is_read`),
  CONSTRAINT `notifications_notifi_recipient_id_d055f3f0_fk_accounts_` FOREIGN KEY (`recipient_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications_notification`
--

LOCK TABLES `notifications_notification` WRITE;
/*!40000 ALTER TABLE `notifications_notification` DISABLE KEYS */;
INSERT INTO `notifications_notification` VALUES (1,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a consultation request.','/consultations/queue/1/',0,'2026-07-17 05:45:51.015090',NULL),(2,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/1/',0,'2026-07-17 05:46:10.451268',NULL),(3,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/1/',0,'2026-07-17 05:50:01.430496',NULL),(4,NULL,'Consultation Completed','Consultation #1 has been completed. ','/consultations/my/1/',0,'2026-07-17 05:50:23.265197',6),(5,'frontdesk','New Consultation Request','Adrian Paylande submitted a consultation request.','/consultations/queue/2/',0,'2026-07-21 02:29:32.526771',NULL),(6,'doctor','Patient Queued for Triage','Adrian Paylande is ready for triage.','/consultations/triage/2/',0,'2026-07-21 02:29:59.234196',NULL),(7,'doctor','Patient Ready for Consultation','Adrian Paylande has been triaged and is ready.','/consultations/prescribe/2/',0,'2026-07-21 02:30:37.919249',NULL),(8,NULL,'Consultation Completed','Consultation #2 has been completed. A follow-up has been recommended.','/consultations/my/2/',0,'2026-07-21 02:31:06.768085',7),(9,'admin','Academic year needs updating','The configured academic year end has passed. Please update the settings for the new term.','/patients/archive/settings/',1,'2026-07-21 06:41:44.858166',NULL),(10,'admin','Academic year needs updating','The configured academic year end has passed. Please update the settings for the new term.','/patients/archive/settings/',1,'2026-07-21 06:41:59.509281',NULL),(11,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/7/',0,'2026-07-23 01:46:52.424251',NULL),(12,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/7/',0,'2026-07-23 01:47:16.112772',NULL),(13,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/7/',0,'2026-07-23 01:47:50.513414',NULL),(14,NULL,'Consultation Completed','Consultation #7 has been completed. ','/consultations/my/7/',0,'2026-07-23 01:48:07.003753',6),(15,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/8/',0,'2026-07-23 03:33:22.854633',NULL),(16,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/8/',0,'2026-07-23 03:33:49.979168',NULL),(17,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/8/',0,'2026-07-23 03:34:39.498721',NULL),(18,NULL,'Consultation Completed','Consultation #8 has been completed. ','/consultations/my/8/',0,'2026-07-23 03:35:01.511123',6),(19,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/9/',0,'2026-07-23 03:44:27.229963',NULL),(20,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/9/',0,'2026-07-23 03:44:55.808017',NULL),(21,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/9/',0,'2026-07-23 03:45:42.156694',NULL),(22,NULL,'Consultation Completed','Consultation #9 has been completed. ','/consultations/my/9/',0,'2026-07-23 03:46:01.910084',6),(23,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/10/',0,'2026-07-23 04:31:39.724586',NULL),(24,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/10/',0,'2026-07-23 04:32:07.051883',NULL),(25,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/10/',0,'2026-07-23 04:32:42.962271',NULL),(26,NULL,'Consultation Completed','Consultation #10 has been completed. ','/consultations/my/10/',0,'2026-07-23 04:32:57.647492',6),(27,'frontdesk','New Consultation Request','Kristel May Baga-an submitted a new consultation request.','/consultations/queue/11/',0,'2026-07-29 05:52:25.524174',NULL),(28,'doctor','Patient Queued for Triage','Kristel May Baga-an is ready for triage.','/consultations/triage/11/',0,'2026-07-29 05:53:38.418621',NULL),(29,'doctor','Patient Ready for Consultation','Kristel May Baga-an has been triaged and is ready.','/consultations/prescribe/11/',0,'2026-07-29 05:54:33.463350',NULL),(30,NULL,'Consultation Completed','Consultation #11 has been completed. ','/consultations/my/11/',1,'2026-07-29 05:55:17.383095',14),(31,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/12/',0,'2026-07-29 09:07:23.611831',NULL),(32,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/12/',0,'2026-07-29 09:07:52.705111',NULL),(33,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/12/',0,'2026-07-29 09:08:32.269174',NULL),(34,NULL,'Consultation Completed','Consultation #12 has been completed. ','/consultations/my/12/',0,'2026-07-29 09:08:46.176873',6),(35,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/13/',0,'2026-07-30 06:44:01.075905',NULL),(36,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/13/',0,'2026-07-30 06:44:54.255056',NULL),(37,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/14/',0,'2026-08-06 05:29:14.208769',NULL),(38,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/14/',0,'2026-08-06 05:29:36.351851',NULL),(39,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/14/',0,'2026-08-06 05:30:33.802592',NULL),(40,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/13/',0,'2026-08-06 06:08:15.623123',NULL),(41,NULL,'Consultation Completed','Consultation #13 has been completed. ','/consultations/my/13/',0,'2026-08-06 06:09:32.272688',6),(42,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/15/',0,'2026-08-06 06:11:41.364280',NULL),(43,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/15/',0,'2026-08-06 06:12:06.326781',NULL),(44,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/15/',0,'2026-08-06 06:12:42.726782',NULL),(45,NULL,'Consultation Completed','Consultation #14 has been completed. ','/consultations/my/14/',0,'2026-08-07 01:09:41.070383',6),(46,NULL,'Consultation Completed','Consultation #15 has been completed. ','/consultations/my/15/',0,'2026-08-07 01:33:00.851175',6),(47,'frontdesk','New Consultation Request','BRADI CARCASONA submitted a new consultation request.','/consultations/queue/16/',0,'2026-08-07 02:07:12.951629',NULL),(48,'doctor','Patient Queued for Triage','BRADI CARCASONA is ready for triage.','/consultations/triage/16/',0,'2026-08-07 02:07:32.591715',NULL),(49,'doctor','Patient Ready for Consultation','BRADI CARCASONA has been triaged and is ready.','/consultations/prescribe/16/',0,'2026-08-07 02:08:33.391744',NULL),(50,NULL,'Consultation Completed','Consultation #16 has been completed. ','/consultations/my/16/',0,'2026-08-11 09:54:28.374970',6);
/*!40000 ALTER TABLE `notifications_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patients_academicyearsettings`
--

DROP TABLE IF EXISTS `patients_academicyearsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients_academicyearsettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `academic_year_end` date NOT NULL,
  `archive_after_months` int unsigned NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `updated_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patients_academicyea_updated_by_id_7d629fb6_fk_accounts_` (`updated_by_id`),
  CONSTRAINT `patients_academicyea_updated_by_id_7d629fb6_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `patients_academicyearsettings_chk_1` CHECK ((`archive_after_months` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patients_academicyearsettings`
--

LOCK TABLES `patients_academicyearsettings` WRITE;
/*!40000 ALTER TABLE `patients_academicyearsettings` DISABLE KEYS */;
INSERT INTO `patients_academicyearsettings` VALUES (1,'2026-08-31',5,'2026-07-21 06:42:40.519627',1);
/*!40000 ALTER TABLE `patients_academicyearsettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patients_patient`
--

DROP TABLE IF EXISTS `patients_patient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients_patient` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `patient_id` varchar(30) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `middle_name` varchar(100) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `sex` varchar(1) NOT NULL,
  `department` varchar(150) NOT NULL,
  `position` varchar(150) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `college_id` bigint DEFAULT NULL,
  `email` varchar(254) NOT NULL,
  `emergency_contact_name` varchar(200) NOT NULL,
  `emergency_contact_phone` varchar(30) NOT NULL,
  `phone` varchar(30) NOT NULL,
  `has_logged_in` tinyint(1) NOT NULL,
  `profile_picture` varchar(100) DEFAULT NULL,
  `archived_at` datetime(6) DEFAULT NULL,
  `archived_reason` varchar(200) NOT NULL,
  `expected_graduation_year` int unsigned DEFAULT NULL,
  `is_archived` tinyint(1) NOT NULL,
  `course_id` bigint DEFAULT NULL,
  `temp_password` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `patient_id` (`patient_id`),
  KEY `patients_pa_patient_927c52_idx` (`patient_id`),
  KEY `patients_pa_last_na_1b32a7_idx` (`last_name`,`first_name`),
  KEY `patients_patient_college_id_c2210cc7_fk_colleges_college_id` (`college_id`),
  KEY `patients_pa_has_log_23d631_idx` (`has_logged_in`),
  KEY `patients_patient_has_logged_in_7f7f6c0a` (`has_logged_in`),
  KEY `patients_pa_is_arch_b8e241_idx` (`is_archived`),
  KEY `patients_patient_is_archived_58e98552` (`is_archived`),
  KEY `patients_patient_course_id_163855bd_fk_colleges_course_id` (`course_id`),
  CONSTRAINT `patients_patient_college_id_c2210cc7_fk_colleges_college_id` FOREIGN KEY (`college_id`) REFERENCES `colleges_college` (`id`),
  CONSTRAINT `patients_patient_course_id_163855bd_fk_colleges_course_id` FOREIGN KEY (`course_id`) REFERENCES `colleges_course` (`id`),
  CONSTRAINT `patients_patient_chk_1` CHECK ((`expected_graduation_year` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patients_patient`
--

LOCK TABLES `patients_patient` WRITE;
/*!40000 ALTER TABLE `patients_patient` DISABLE KEYS */;
INSERT INTO `patients_patient` VALUES (2,'202301028','BRADI','','CARCASONA','F','','',1,'2026-07-17 05:45:50.559662','2026-07-17 05:45:50.559755',1,'carcasonabradi@gmail.com','CARCASONA, BRADI','09690956233','09171234501',1,'patients/inbound871744176630484561.jpg',NULL,'',2027,0,NULL,'6798'),(3,'202300316','Adrian','','Paylande','M','','',1,'2026-07-21 02:29:32.058878','2026-07-21 02:29:32.059285',1,'sample@gmail.com','Sample','09690956333','09690956644',1,'',NULL,'',2027,0,1,'8402'),(8,'202300055','Kylle','Ian Dicen','Acibron','M','','',1,'2026-07-29 05:23:31.470548','2026-07-29 05:23:31.470570',1,'kylleacibron@gmail.com','Kylle Acibron','09455470173','09455470173',1,'',NULL,'',2027,0,1,''),(9,'202300627','Kristel May','','Baga-an','F','','',1,'2026-07-29 05:51:39.444975','2026-07-29 05:51:39.445042',4,'bagaankristelmay@gmail.com','Bradi Carcasona','09690956344','09354628604',0,'patients/inbound1196389266334093314.jpg',NULL,'',2027,0,NULL,''),(10,'12345678','Bradi','','Carcasona','M','SAS','Intructor',1,'2026-07-30 03:46:39.983281','2026-07-30 03:46:39.983301',1,'bradicarcasona21@gmail.com','Denia','09690956344','09690956344',0,'',NULL,'',NULL,0,NULL,''),(11,'87654321','Bradi','','Carcasona','M','SAS','',1,'2026-07-30 03:49:03.577238','2026-07-30 03:49:03.577266',NULL,'bradicarcasona20@gmail.com','sample','09690956333','09690956344',0,'',NULL,'',NULL,0,NULL,'');
/*!40000 ALTER TABLE `patients_patient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patients_patientprofile`
--

DROP TABLE IF EXISTS `patients_patientprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients_patientprofile` (
  `patient_id` bigint NOT NULL,
  `birthday` date DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `address` varchar(300) NOT NULL,
  `blood_type` varchar(10) NOT NULL,
  `existing_conditions` longtext NOT NULL,
  `known_allergies` longtext NOT NULL,
  `profile_completed` tinyint(1) NOT NULL,
  `arthritis` tinyint(1) NOT NULL,
  `asthma` tinyint(1) NOT NULL,
  `bcg` tinyint(1) NOT NULL,
  `cardiac_problems` tinyint(1) NOT NULL,
  `civil_status` varchar(20) NOT NULL,
  `current_medications` longtext NOT NULL,
  `diabetes` tinyint(1) NOT NULL,
  `dpt` tinyint(1) NOT NULL,
  `height_cm` decimal(5,1) DEFAULT NULL,
  `hepatitis_b` tinyint(1) NOT NULL,
  `hypertension` tinyint(1) NOT NULL,
  `immunization_others` longtext NOT NULL,
  `measles` tinyint(1) NOT NULL,
  `opv` tinyint(1) NOT NULL,
  `other_conditions` longtext NOT NULL,
  `previous_hospitalizations` longtext NOT NULL,
  `previous_illnesses` longtext NOT NULL,
  `religion` varchar(100) NOT NULL,
  `tt` tinyint(1) NOT NULL,
  `vices` longtext NOT NULL,
  `weight_kg` decimal(5,1) DEFAULT NULL,
  `year_level` varchar(20) NOT NULL,
  PRIMARY KEY (`patient_id`),
  CONSTRAINT `patients_patientprof_patient_id_a7ee6137_fk_patients_` FOREIGN KEY (`patient_id`) REFERENCES `patients_patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patients_patientprofile`
--

LOCK TABLES `patients_patientprofile` WRITE;
/*!40000 ALTER TABLE `patients_patientprofile` DISABLE KEYS */;
INSERT INTO `patients_patientprofile` VALUES (2,'2004-08-31','2026-08-07 02:08:33.349284','','B+','','',1,0,0,1,0,'Single','',0,1,NULL,0,1,'',0,0,'','','','',0,'',NULL,'4th Year'),(3,'0004-01-07','2026-08-11 09:51:41.484073','','','','',1,0,0,0,0,'','',0,0,NULL,1,1,'',0,0,'','','','',0,'',NULL,'4th Year'),(8,'2005-01-15','2026-07-29 05:23:31.476007','Claro M. Recto Street, Purok 4 Barangay Tinago, Bayawan City','O+','','',1,0,0,0,0,'Single','',0,0,157.0,0,0,'',0,0,'','','','',0,'',58.7,'4th Year'),(9,'2004-05-13','2026-07-29 06:04:48.817918','Bayawan City, Negros Oriental','Unknown','','',1,0,0,0,0,'Single','',0,0,161.0,0,1,'',0,0,'yearning','','','Roman Catholic',0,'',43.5,'4th Year'),(10,'2004-01-30','2026-07-30 03:46:39.991258','Claro M. Rectro street','','','',1,0,0,0,0,'Single','',0,0,NULL,0,0,'',0,0,'','','','',0,'',NULL,''),(11,'2000-07-30','2026-07-30 03:49:03.580465','Claro M. Rectro street','','','',1,0,0,0,0,'','',0,0,NULL,0,0,'',0,0,'','','','',0,'',NULL,'');
/*!40000 ALTER TABLE `patients_patientprofile` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-12  0:11:24
