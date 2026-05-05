from models.pretrained.pan_validation import verify_pan_card, model as pan_model

print(f"PAN Model Status: {'Loaded' if pan_model else 'Not Available'}")
print("-" * 50)

# Use correct image path
image_path = "test_images/pan1.jpeg"

import os
if not os.path.exists(image_path):
    # Try alternative paths
    alt_paths = ["sentinel_env/pan1.jpeg", "pan1.jpeg", "test_images/pan_test.jpg"]
    for alt in alt_paths:
        if os.path.exists(alt):
            image_path = alt
            break

print(f"Testing image: {image_path}")
print("-" * 50)

score, results = verify_pan_card(image_path)

print(f"\nPAN Validation Score: {score:.1f}%")
print("\nField Details:")
print("-" * 50)

for r in results:
    status = "✓ Valid" if r['valid'] else "✗ Invalid"
    conf = f"{r['confidence']:.1%}" if r.get('confidence') else "N/A"
    text = r['text'][:30] + "..." if len(r.get('text', '')) > 30 else r.get('text', '')
    print(f"  {r['field']:<15} [{conf}] '{text}' {status}")

print("-" * 50)
print(f"Overall: {sum(1 for r in results if r['valid'])}/{len(results)} fields valid")