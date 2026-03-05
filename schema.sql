DROP DATABASE IF EXISTS chat_app;

CREATE DATABASE IF NOT EXISTS chat_app;
USE chat_app;

CREATE TABLE IF NOT EXISTS Users (
    user_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    logged_in BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS PrivateMessages (
    message_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS GroupChat (
    group_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    group_name VARCHAR(255) NOT NULL UNIQUE,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS GroupChatMembers (
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES GroupChat(group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS GroupMessages (
    message_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    group_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES GroupChat(group_id),
    FOREIGN KEY (sender_id) REFERENCES Users(user_id)
);

ALTER TABLE PrivateMessages 
    ADD COLUMN media LONGBLOB;

ALTER TABLE GroupMessages
    ADD COLUMN media LONGBLOB;

-- We make text message nullable to allow for messages that only contain media (like images or videos) without any accompanying text.
ALTER TABLE PrivateMessages
    MODIFY COLUMN message_text TEXT NULL;

ALTER TABLE PrivateMessages
    ADD COLUMN delivered TINYINT(1) NOT NULL DEFAULT 0,
    ADD COLUMN delivered_at TIMESTAMP NULL;