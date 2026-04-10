import os
import fitz  # PyMuPDF
from tqdm import tqdm  # For progress bar, install with: pip install tqdm


def image_to_pdf(image_path, pdf_path):
    """Convert a single image to PDF"""
    try:
        # Create a new PDF document
        pdf_document = fitz.open()
        # Open the image
        image = fitz.open(image_path)
        # Get image size
        rect = image[0].rect
        # Create a new page with the same size as the image
        pdf_page = pdf_document.new_page(width=rect.width, height=rect.height)
        # Insert the image into the page
        pdf_page.insert_image(rect, filename=image_path)
        # Save the PDF
        pdf_document.save(pdf_path)
        pdf_document.close()
        print(f"Successfully converted: {image_path} -> {pdf_path}")
    except Exception as e:
        print(f"Failed to convert: {image_path} - Error: {str(e)}")


def is_image_file(filename):
    """Check if the file is a supported image format"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    return any(filename.lower().endswith(ext) for ext in image_extensions)


def batch_images_to_pdfs(input_dir, output_dir=None):
    """
    Recursively process all images in a directory and convert them to PDFs

    Args:
    input_dir: Input image directory
    output_dir: Output PDF directory. If None, a "pdfs" subdirectory will be created in the input directory.
    """
    # If output directory is not specified, create a "pdfs" directory in the input directory
    if output_dir is None:
        output_dir = os.path.join(input_dir, "pdfs")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get all image files
    image_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if is_image_file(file):
                image_files.append(os.path.join(root, file))

    if not image_files:
        print(f"No image files found in {input_dir}")
        return

    print(f"Found {len(image_files)} image files, starting conversion...")

    # Process each image
    for image_path in tqdm(image_files, desc="Conversion Progress"):
        # Calculate relative path to maintain directory structure in output
        rel_path = os.path.relpath(image_path, input_dir)
        rel_dir = os.path.dirname(rel_path)
        # Create corresponding output subdirectory
        output_subdir = os.path.join(output_dir, rel_dir)
        os.makedirs(output_subdir, exist_ok=True)

        # Get filename without extension
        filename = os.path.splitext(os.path.basename(image_path))[0]
        # Generate PDF path
        pdf_path = os.path.join(output_subdir, f"{filename}.pdf")

        # Convert image to PDF
        image_to_pdf(image_path, pdf_path)

    print(f"Conversion complete! All PDF files are saved in: {output_dir}")


if __name__ == "__main__":
    # Example usage
    input_directory = "your_image_directory_path"  # Replace with your image directory path
    output_directory = "your_output_directory_path" # Replace with output directory path, or None to use default

    batch_images_to_pdfs(input_directory, output_directory)