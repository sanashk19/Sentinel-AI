from models.pretrained.certificate_validation import verify_certificate
import os

# Use correct image path
image_path = "test_images/image.png"

if not os.path.exists(image_path):
    # Try alternative paths
    alt_paths = ["certificate.jpg", "test_images/image.png", "test_images/certificate.png"]
    for alt in alt_paths:
        if os.path.exists(alt):
            image_path = alt
            break

print(f"Testing image: {image_path}")
print("-" * 50)

score, results = verify_certificate(image_path)

print(f"\nCertificate Validation Score: {score:.1f}%")
print("\nField Details:")
print("-" * 50)

for r in results:
    status = "✓ Valid" if r.get('valid') else "✗ Invalid"
    conf = f"{r.get('confidence', 0):.1%}" if r.get('confidence') else "N/A"
    text = r.get('text', '')[:30] if r.get('text') else ''
    print(f"  {r['field']:<20} [{conf}] '{text}' {status}")

print("-" * 50)
print(f"Overall: {sum(1 for r in results if r.get('valid'))}/{len(results)} detections valid")