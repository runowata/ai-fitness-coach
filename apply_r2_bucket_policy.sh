#!/bin/bash

# Script to apply bucket policy for public access to R2 motivational images
# This needs to be run with your R2 credentials

set -e

echo "=== Applying R2 Bucket Policy for Public Access ==="
echo ""
echo "This will allow public read access to photos/progress/ folder only."
echo "All other files remain private."
echo ""

# R2 Configuration
BUCKET_NAME="ai-fitness-media"
ENDPOINT_URL="https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com"

# Create bucket policy
cat > bucket_policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadMotivationalImages",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ai-fitness-media/photos/progress/*"
    }
  ]
}
EOF

echo "Bucket policy content:"
cat bucket_policy.json
echo ""

echo "To apply this policy, run:"
echo ""
echo "aws s3api put-bucket-policy \\"
echo "  --bucket $BUCKET_NAME \\"
echo "  --policy file://bucket_policy.json \\"
echo "  --endpoint-url $ENDPOINT_URL"
echo ""

echo "After applying, test with:"
echo "curl -I https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg"
echo ""
echo "Should return HTTP/1.1 200 OK (not 401 Unauthorized)"

# Cleanup
# rm bucket_policy.json