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
$post=$_POST["date"];
$sql = "SELECT user_id,created_at FROM stream where created_at>=".$post;
$result = $conn->query($sql);

if ($result->num_rows > 0) {
     // output data of each row
	$rows = array();
	while($r = mysqli_fetch_assoc($result)) {
	    $rows[] = $r;
	}
	echo json_encode($rows);
     // while($row = $result->fetch_assoc()) {
     //     echo "<br> id: ". $row["user_id"]. " - Name: ". $row["created_at"]. "<br>";
     // }
} else {
     echo "0 results";
}

$conn->close();
?>  