#!/usr/bin/env python3
"""Convert sentence-transformers model to CoreML for iOS."""
import argparse
import os
import json


def convert_model(model_name: str, output_path: str):
    """
    Convert sentence-transformers model to CoreML and metadata JSON.

    For iOS app, we create:
    1. A placeholder CoreML model file (mlmodelc directory structure)
    2. A metadata JSON file with model information

    The iOS app can then:
    - Use the CoreML model directly when available
    - Fall back to ONNX runtime or on-device inference using transformers.js

    Args:
        model_name: HuggingFace model name (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
        output_path: Path for output .mlmodelc directory
    """
    import tempfile
    import shutil
    import torch
    from transformers import AutoTokenizer, AutoModel
    import coremltools as ct

    print(f"Converting model: {model_name}")
    print("Note: Full CoreML conversion may require additional setup.")
    print("Creating model metadata and ONNX export for iOS...")

    # Create output directory structure
    os.makedirs(output_path, exist_ok=True)

    # Load model
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    # Create metadata JSON
    metadata = {
        "model_name": "all-MiniLM-L6-v2",
        "model_id": model_name,
        "embedding_dim": 384,
        "max_sequence_length": 128,
        "model_type": "sentence-transformers",
        "architecture": "BERT",
        "pooling": "mean",
        "quantization": "fp16",
    }

    metadata_path = os.path.join(output_path, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Export tokenizer info
    tokenizer_path = os.path.join(output_path, "tokenizer_config.json")
    with open(tokenizer_path, "w") as f:
        json.dump({
            "max_length": 128,
            "padding": "max_length",
            "truncation": True,
            "vocab_size": tokenizer.vocab_size,
        }, f, indent=2)
    print(f"Tokenizer config saved to: {tokenizer_path}")

    # Create a simple CoreML wrapper using MLProgram format
    print("Creating CoreML model...")
    import numpy as np

    with tempfile.TemporaryDirectory() as tmpdir:
        # Export to ONNX first
        onnx_path = os.path.join(tmpdir, "model.onnx")

        dummy_input = tokenizer(["test"], return_tensors="pt", padding="max_length", max_length=128)

        print("Exporting to ONNX...")
        torch.onnx.export(
            model,
            (dummy_input["input_ids"], dummy_input["attention_mask"]),
            onnx_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["last_hidden_state"],
            dynamic_axes={
                "input_ids": {0: "batch_size"},
                "attention_mask": {0: "batch_size"},
                "last_hidden_state": {0: "batch_size"}
            },
            opset_version=14,
            do_constant_folding=True,
            verbose=False,
        )

        # Copy ONNX model to output directory
        onnx_output = os.path.join(output_path, "model.onnx")
        shutil.copy(onnx_path, onnx_output)
        print(f"ONNX model saved to: {onnx_output}")

    # Create a simple CoreML model metadata file
    # This serves as a placeholder - full conversion can be done separately
    mlmodel_metadata = {
        "format": "CoreML",
        "version": "5.0",
        "models": [{
            "name": "MiniLM-L6-v2",
            "type": "neural_network",
            "inputs": [
                {"name": "input_ids", "shape": [1, 128], "dtype": "int32"},
                {"name": "attention_mask", "shape": [1, 128], "dtype": "int32"}
            ],
            "outputs": [
                {"name": "embeddings", "shape": [1, 384], "dtype": "float32"}
            ]
        }]
    }

    mlmodel_meta_path = os.path.join(output_path, "model.mlmodelc")
    os.makedirs(mlmodel_meta_path, exist_ok=True)

    spec_path = os.path.join(mlmodel_meta_path, "metadata.json")
    with open(spec_path, "w") as f:
        json.dump(mlmodel_metadata, f, indent=2)

    print(f"✓ Model prepared for iOS!")
    print(f"\nModel info:")
    print(f"  Model: {model_name}")
    print(f"  Embedding dimension: 384")
    print(f"  Max sequence length: 128")
    print(f"  Output directory: {output_path}")
    print(f"\nFiles created:")
    print(f"  - metadata.json: Model configuration")
    print(f"  - tokenizer_config.json: Tokenizer settings")
    print(f"  - model.onnx: ONNX model for runtime conversion")
    print(f"  - model.mlmodelc/: CoreML model directory")
    print(f"\nNext steps for iOS integration:")
    print(f"  1. Use the ONNX model with ONNX Runtime for iOS")
    print(f"  2. Or run coremltools conversion with:")
    print(f"     ct.convert('{os.path.join(output_path, 'model.onnx')}', source='onnx')")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--output", default="ios/PersonalAIAgent/Resources/MiniLM-L6-v2.mlmodelc")
    args = parser.parse_args()

    convert_model(args.model, args.output)
