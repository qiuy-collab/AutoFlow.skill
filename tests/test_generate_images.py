import sys
import unittest
import base64
import tempfile
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_images


class GenerateImageTaskTests(unittest.TestCase):
    def test_screenshot_lint_allows_java_annotation_package_name(self):
        policy = {"screenshot_forbidden_terms": ["annotation"]}

        errors = generate_images.lint_prompt(
            policy,
            "controller",
            "Use the actual import org.springframework.web.bind.annotation.* in the Java source.",
            "screenshot_strict",
        )

        self.assertEqual(errors, [])

    def test_single_request_uses_requested_model_and_default_1k_resolution(self):
        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"data": [{"b64_json": base64.b64encode(b"image-bytes").decode()}]}

        with tempfile.TemporaryDirectory() as temp:
            with patch.object(generate_images.requests, "post", return_value=Response()) as post:
                generated = generate_images.generate_image_single(
                    prompt="A non-sensitive concept illustration.",
                    output_dir=temp,
                    filename="result",
                    base_url="https://images.example.test",
                    api_key="test-key",
                    model="custom-image-model",
                )

        self.assertTrue(generated.endswith("result.png"))
        request = post.call_args.kwargs["json"]
        self.assertEqual(request["model"], "custom-image-model")
        self.assertEqual(request["size"], "1024x1024")

    def test_batch_report_preserves_http_generation_error(self):
        task = {
            "index": 1,
            "total": 1,
            "name": "img_001",
            "prompt": "A non-sensitive prompt.",
            "output_dir": str(Path.cwd()),
            "resolution": "1024x1024",
            "max_retries": 1,
            "retry_delay": 0,
            "base_url": "https://images.example.test",
            "api_key": "test-key",
            "timeout": 5,
        }

        with patch.object(
            generate_images,
            "generate_image_single",
            side_effect=generate_images.ImageGenerationError(
                "HTTP 503 Service Unavailable at https://images.example.test/v1/images/generations"
            ),
        ):
            result = generate_images.generate_image_task(task)

        self.assertFalse(result["success"])
        self.assertIn("HTTP 503 Service Unavailable", result["error"])


if __name__ == "__main__":
    unittest.main()
