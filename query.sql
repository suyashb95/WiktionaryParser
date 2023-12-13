SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


-- --------------------------------------------------------

--
-- Table structure for table `{dataset_table}`
--

CREATE TABLE IF NOT EXISTS `{dataset_table}` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `text` varchar(1023) NOT NULL,
  `label` varchar(255) NOT NULL,
  `dataset_name` varchar(255) DEFAULT NULL,
  `task` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `{word_table}`
--

CREATE TABLE IF NOT EXISTS `{word_table}` (
  `id` varchar(64) NOT NULL,
  `word` varchar(255) DEFAULT NULL,
  `query` varchar(255) DEFAULT NULL,
  `language` varchar(255) DEFAULT NULL,
  `etymology` text DEFAULT NULL,
  `wikiUrl` text DEFAULT NULL,
  `isDerived` BOOLEAN,
  PRIMARY KEY (`id`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
-- ALTER TABLE `{word_table}` ADD INDEX(`word`);
-- --------------------------------------------------------

--
-- Table structure for table `{definitions_table}`
--

CREATE TABLE IF NOT EXISTS `{definitions_table}` (
  `id` varchar(64) NOT NULL,
  `wordId` varchar(64) NOT NULL,
  `partOfSpeech` varchar(16) NOT NULL,
  `text` varchar(1024) NOT NULL,
  `headword` varchar(256) NOT NULL , 
  -- `dialect` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`(64)),
  CONSTRAINT fk_wordId FOREIGN KEY (wordId)  
  REFERENCES {word_table}(id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `appendix`
--

CREATE TABLE IF NOT EXISTS `appendix` (
  `id` varchar(64) NOT NULL,
  `label` varchar(255) NOT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `wikiUrl` varchar(255) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL ,
  PRIMARY KEY (`id`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `{definitions_table}_apx`
--

CREATE TABLE IF NOT EXISTS `{definitions_table}_apx` (
  `definitionId` varchar(64) NOT NULL,
  `appendixId` varchar(64) NOT NULL , 
  CONSTRAINT fk_definitionId FOREIGN KEY (definitionId)  
  REFERENCES {definitions_table}(id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE , 
  CONSTRAINT fk_definitionApx FOREIGN KEY (appendixId)  
  REFERENCES appendix (id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `{edge_table}`
--

CREATE TABLE IF NOT EXISTS `{edge_table}` (
  `headDefinitionId` varchar(64) NOT NULL,
  `wordId` varchar(64) DEFAULT NULL,
  `relationshipType` varchar(64) DEFAULT NULL , 
  CONSTRAINT fk_definitionIdRel FOREIGN KEY (headDefinitionId)  
  REFERENCES {definitions_table}(id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE  ,

  CONSTRAINT fk_wordIdRel FOREIGN KEY (wordId)  
  REFERENCES {word_table}(id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE IF NOT EXISTS `categories` (
  `id` VARCHAR(64) NOT NULL , 
  `title` TEXT NOT NULL , 
  `text` TEXT NOT NULL , 
  `sourceList` VARCHAR(64) NOT NULL , 
  `wikiUrl` TEXT NOT NULL , 
  PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `{definitions_table}_apx`
--

CREATE TABLE IF NOT EXISTS `word_categories` (
  `wordId` varchar(64) NOT NULL,
  `categoryId` varchar(64) NOT NULL , 
  CONSTRAINT fk_wordCatgId FOREIGN KEY (wordId)  
  REFERENCES {word_table}(id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE , 
  CONSTRAINT fk_wordCatg FOREIGN KEY (categoryId)  
  REFERENCES categories (id)  
  ON DELETE CASCADE  
  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `{definitions_table}_apx`
--
CREATE TABLE IF NOT EXISTS `examples` (
    id INT PRIMARY KEY AUTO_INCREMENT,
    definitionId varchar(64) NOT NULL , 
    quotation TEXT NOT NULL,
    transliteration TEXT NULL,
    translation TEXT NULL,
    source TEXT NULL,
    example_text TEXT NOT NULL,
    
    CONSTRAINT fk_exampleDef FOREIGN KEY (definitionId) 
    REFERENCES {definitions_table} (id)
    ON DELETE CASCADE  
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;