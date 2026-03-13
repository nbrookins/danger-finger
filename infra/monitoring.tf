# SNS topic for monitoring alerts.
resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# EC2 system status alarm with AWS-native recovery action.
resource "aws_cloudwatch_metric_alarm" "ec2_status_check" {
  alarm_name          = "${var.project}-ec2-status-check"
  alarm_description   = "Recover the EC2 instance if AWS system checks fail."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed_System"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  alarm_actions = [
    "arn:aws:automate:${var.aws_region}:ec2:recover",
    aws_sns_topic.alerts.arn,
  ]
}

resource "aws_iam_role_policy" "lambda_monitoring" {
  name = "monitoring"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ssm:SendCommand"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "health_check" {
  function_name    = "${var.project}-health-check"
  role             = aws_iam_role.lambda.arn
  handler          = "health_check.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      EC2_URL      = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_instance.app.public_ip}:8081"
      INSTANCE_ID  = aws_instance.app.id
      PROJECT_NAME = var.project
      METRIC_NAME  = "AppHealthFailed"
      METRIC_NS    = "DangerFinger/Monitoring"
    }
  }
}

resource "aws_cloudwatch_event_rule" "health_check_schedule" {
  name                = "${var.project}-health-check"
  description         = "Run the application health check every 5 minutes."
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "health_check_lambda" {
  rule      = aws_cloudwatch_event_rule.health_check_schedule.name
  target_id = "health-check-lambda"
  arn       = aws_lambda_function.health_check.arn
}

resource "aws_lambda_permission" "allow_eventbridge_health_check" {
  statement_id  = "AllowEventBridgeHealthCheck"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.health_check_schedule.arn
}

resource "aws_cloudwatch_metric_alarm" "app_health_check" {
  alarm_name          = "${var.project}-app-health-check"
  alarm_description   = "Alert when the app health check fails twice in a row."
  namespace           = "DangerFinger/Monitoring"
  metric_name         = "AppHealthFailed"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
}
