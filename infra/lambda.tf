# Lambda function for S3 read API (replaces template.yaml SAM definition)

resource "aws_iam_role" "lambda" {
  name = "${var.project}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "s3-read"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:HeadObject"]
      Resource = "${data.aws_s3_bucket.app.arn}/*"
    }]
  })
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/.build/lambda.zip"
}

resource "aws_lambda_function" "s3_read" {
  function_name    = "${var.project}-s3-read"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 15
  memory_size      = 256
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
    }
  }

  layers = [aws_lambda_layer_version.brotli.arn]
}

# Brotli dependency as a Lambda layer (not in standard runtime)
resource "aws_lambda_layer_version" "brotli" {
  layer_name          = "${var.project}-brotli"
  description         = "Brotli compression library for Lambda"
  compatible_runtimes = ["python3.12"]
  filename            = "${path.module}/.build/brotli-layer.zip"
  source_code_hash    = filebase64sha256("${path.module}/.build/brotli-layer.zip")
}

# --- API Gateway HTTP API ---

resource "aws_apigatewayv2_api" "read" {
  name          = "${var.project}-read-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_headers = ["Content-Type", "Authorization"]
    allow_methods = ["GET", "OPTIONS"]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.read.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.s3_read.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "configs" {
  api_id    = aws_apigatewayv2_api.read.id
  route_key = "GET /configs/{cfghash}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "profiles" {
  api_id    = aws_apigatewayv2_api.read.id
  route_key = "GET /profiles/{userhash}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "bundle" {
  api_id    = aws_apigatewayv2_api.read.id
  route_key = "GET /render/{cfghash}/bundle.zip"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.read.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_read.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.read.execution_arn}/*/*"
}
