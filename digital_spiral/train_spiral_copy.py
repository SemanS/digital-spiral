import torch
from torch import nn
from torch.optim import Adam

from x_transformers import Decoder, TransformerWrapper, AutoregressiveWrapper
from digital_spiral.spiral_mask import build_spiral_mask


def generate_batch(batch_size: int, half_seq_len: int, vocab_size: int, device: torch.device):
    """Generate a batch for the copy task.

    Each sample consists of a random sequence of ``half_seq_len`` tokens, a delimiter token (vocab_size-1),
    and ``half_seq_len`` padding tokens (zeros). The target positions correspond to the tokens after the
    delimiter; positions before the delimiter are ignored with label -100.
    """
    left = torch.randint(0, vocab_size - 1, (batch_size, half_seq_len), device=device)
    delim = torch.full((batch_size, 1), vocab_size - 1, dtype=torch.long, device=device)
    right = torch.zeros((batch_size, half_seq_len), dtype=torch.long, device=device)
    inp = torch.cat([left, delim, right], dim=1)
    # ignore label for left part and delimiter
    ignore = torch.full((batch_size, half_seq_len + 1), -100, device=device)
    target = torch.cat([ignore, left], dim=1)
    return inp, target


def train_model(
    vocab_size: int = 16,
    half_seq_len: int = 16,
    dim: int = 128,
    depth: int = 4,
    heads: int = 4,
    local_window: int = 4,
    spiral_offsets: list | None = None,
    bands: int = 1,
    epochs: int = 5,
    batch_size: int = 32,
) -> None:
    """Train a small Transformer on the copy task using a spiral attention mask."""
    seq_len = half_seq_len * 2 + 1
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if spiral_offsets is None:
        spiral_offsets = [half_seq_len + 1]

    mask = build_spiral_mask(seq_len, local_window, spiral_offsets, bands, device=device)
    # invert mask: positions marked False (not allowed) become True (mask out)
    additive_mask = ~mask

    decoder = Decoder(dim=dim, depth=depth, heads=heads, max_seq_len=seq_len, causal=True)
    net = TransformerWrapper(num_tokens=vocab_size, max_seq_len=seq_len, attn_layers=decoder)
    model = AutoregressiveWrapper(net).to(device)

    optimizer = Adam(model.parameters(), lr=3e-4)
    criterion = nn.CrossEntropyLoss(ignore_index=-100)
    steps_per_epoch = 100

    for epoch in range(epochs):
        total_loss = 0.0
        for _ in range(steps_per_epoch):
            inp, target = generate_batch(batch_size, half_seq_len, vocab_size, device)
            # expand mask to [batch, heads=1, seq_len, seq_len]
            attn_mask = additive_mask.unsqueeze(0).unsqueeze(0).expand(batch_size, 1, seq_len, seq_len)
            logits = model(inp, return_logits=True, attn_mask=attn_mask)
            loss = criterion(logits.view(-1, vocab_size), target.view(-1))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1} loss: {total_loss / steps_per_epoch:.4f}")

    # Evaluation
    with torch.no_grad():
        inp, target = generate_batch(batch_size, half_seq_len, vocab_size, device)
        attn_mask = additive_mask.unsqueeze(0).unsqueeze(0).expand(batch_size, 1, seq_len, seq_len)
        logits = model(inp, return_logits=True, attn_mask=attn_mask)
        preds = logits.argmax(dim=-1)
        # compute accuracy on copied region
        correct = (preds[:, half_seq_len + 1 :] == inp[:, : half_seq_len]).float()
        copy_acc = correct.mean().item()
        print(f"Copy accuracy: {copy_acc * 100:.2f}%")


if __name__ == "__main__":
    train_model()
