import torch


def build_spiral_mask(seq_len: int, local_window: int = 4, spiral_offsets: list | None = None, bands: int = 1, device=None) -> torch.BoolTensor:
    """Build a boolean mask for spiral attention.

    Args:
        seq_len (int): total sequence length.
        local_window (int): number of previous tokens available (causal + local). Each token can attend to tokens within this window on its left.
        spiral_offsets (list[int] | None): list of relative offsets for spiral connections; each token i will be connected to token i - offset.
        bands (int): number of neighboring indices to include on each side of the central spiral connection (i.e., thickness of the spiral). Example bands=1 adds i-(offset+1) and i-(offset-1).
        device (torch.device | str | None): device on which to construct the mask.

    Returns:
        torch.BoolTensor: attention mask of shape (seq_len, seq_len), where True indicates allowed attention.
    """
    if spiral_offsets is None:
        raise ValueError(
            "spiral_offsets must be provided: specify relative index to add connections, e.g. [seq_len // 2 + 1]"
        )

    device = device if device is not None else "cpu"

    # initialize with False
    mask = torch.zeros(seq_len, seq_len, dtype=torch.bool, device=device)

    # basic causal + local window
    for i in range(seq_len):
        # ensure we don't go below 0
        start = max(0, i - local_window)
        mask[i, start : i + 1] = True

    # add spiral offsets
    for offset in spiral_offsets:
        for i in range(seq_len):
            j = i - offset
            if 0 <= j < seq_len:
                # center connection
                mask[i, j] = True
                # additional bands on either side
                for b in range(1, bands + 1):
                    # above central
                    jj = j + b
                    if 0 <= jj < seq_len:
                        mask[i, jj] = True
                    # below central
                    jj = j - b
                    if 0 <= jj < seq_len:
                        mask[i, jj] = True

    return mask
