output "public_ip" {
  description = "Public IP address of the monitoring server"
  value       = aws_instance.monitor_server.public_ip
}

output "app_url" {
  description = "URL to access the monitoring dashboard"
  value       = "http://${aws_instance.monitor_server.public_ip}"
}
