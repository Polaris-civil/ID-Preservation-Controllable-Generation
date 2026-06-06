# Safety and Responsible Use

This project is a research and prototyping scaffold for identity-preserving
image generation. Real deployments should add policy controls before exposing
the system to end users.

Recommended controls:

- Require consent for every non-public reference image.
- Store consent metadata with the generation manifest.
- Watermark or label generated outputs when they may be mistaken for real photos.
- Block impersonation, harassment, sexual content involving real people, and
  political or financial misinformation.
- Keep audit logs for prompts, references, adapters, seeds, and output hashes.
- Run face/identity similarity checks only for quality assurance and consented
  subjects.

The repository's mock backend does not create photorealistic output, but the
same workflow can be connected to powerful image models. Treat the production
version as sensitive software.
