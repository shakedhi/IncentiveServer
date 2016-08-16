<?php
$servername = "localhost";
$username = "root";
$password = "9670";
$dbname = "streamer";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);
// Check connection
if ($conn->connect_error) {
     die("Connection failed: " . $conn->connect_error);
} 
$user=$_POST["username"];
$pass=$_POST["passwd"];


$stmt = $conn->prepare('SELECT * FROM users WHERE username = ?');
$stmt->bind_param('s', $username);

$stmt->execute();

$result = $stmt->get_result();
while ($row = $result->fetch_assoc()) {
    // do something with $row
     echo $row['passwd'];
     if($row['passwd']==$pass)
          echo "true";
}
echo $pass;
//echo "false";


$conn->close();
?>  