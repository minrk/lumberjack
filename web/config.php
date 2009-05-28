<?php

class config
{
	static $dbms_host = 		"mysql.lassam.net";
	static $dbms_port = 		"";
	static $dbms_database = 	"pierc";
	static $dbms_user = 		"pierc";
	static $dbms_pass = 		"thedayofthetriffids";
	
	static $default_channel =	"sfucsss";
	static $default_number_of_lines = 50;
	
	static function get_db()
	{
		return new pie_db( config::$dbms_host, config::$dbms_port, config::$dbms_database, config::$dbms_user, config::$dbms_pass );
	}
}


?>