from models.pretrained.field_validation import validate_document_fields, ocr_backend

print(f"OCR Backend: {ocr_backend or 'None (install easyocr or tesseract)'}")
print("-" * 50)

# Use the test image from test_images directory
score, results = validate_document_fields("test_images/image.png")

print(f"\nField Validation Score: {score:.1f}%")
print("\nField Details:")
print("-" * 50)

for r in results:
    status = "✓ Valid" if r['valid'] else "✗ Invalid"
    conf = f"{r['confidence']:.1%}"
    text = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
    print(f"  {r['field']:<15} [{conf}] '{text}' {status}")

print("-" * 50)
print(f"Overall: {sum(1 for r in results if r['valid'])}/{len(results)} fields valid")