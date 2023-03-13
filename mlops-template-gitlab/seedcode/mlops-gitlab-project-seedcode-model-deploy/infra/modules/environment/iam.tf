resource "aws_iam_role" "sagemaker_role" {
  name = "${var.service_name}-sagemaker-role"
  assume_role_policy = file("${path.module}/policies/sagemaker.json")
}

resource "aws_iam_role_policy_attachment" "sagemaker_role_policy" {
  role = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_sagemaker_role_policy" {
  role = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role_policy_attachment" "ecs_sagemaker_role_policy" {
  role = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_sagemaker_role_policy" {
  role = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
