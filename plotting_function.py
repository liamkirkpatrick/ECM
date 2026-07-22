# Import packages
import os
import glob

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


def make_run_plot(
    xinput,
    array,
    ydim,
    acordc,
    run_date,
    core_section_face,
    show=False,
    save_root=os.path.join('..', 'figures'),
    button_mask=None,
    track_limits=None,
):
    """Create the saved ECM summary figure and return the figure plus path."""
    array = np.asarray(array)
    ydim = np.asarray(ydim)
    xinput = np.asarray(xinput)

    if array.ndim == 1:
        array = array[:, np.newaxis]

    track_count = min(array.shape[1], len(ydim))
    cmap = matplotlib.colormaps.get_cmap('coolwarm')

    fig, (left_ax, right_ax) = plt.subplots(1, 2, figsize=(12.6, 7.2), dpi=100)

    if xinput.ndim == 1:
        depth_centers = xinput.astype(float)
    else:
        depth_centers = np.nanmean(xinput.astype(float), axis=1)

    valid_rows = np.isfinite(depth_centers) & np.any(np.isfinite(array), axis=1)
    if not np.any(valid_rows):
        raise ValueError('No finite data were available for plotting.')

    depth_centers = depth_centers[valid_rows]
    array = array[valid_rows, :track_count]
    if button_mask is None:
        button_mask = np.zeros_like(array, dtype=bool)
    else:
        button_mask = np.asarray(button_mask)
        if button_mask.ndim == 1:
            button_mask = button_mask[:, np.newaxis]
        button_mask = np.where(np.isfinite(button_mask.astype(float)), button_mask.astype(bool), False)
        button_mask = button_mask[valid_rows, :track_count]
    xinput = xinput[valid_rows, ...]

    for track_index in range(track_count):
        if xinput.ndim > 1:
            xvec = xinput[:, track_index]
        else:
            xvec = xinput
        yvec = array[:, track_index]
        left_ax.plot(
            yvec,
            xvec,
            color=cmap(track_index / max(track_count, 1)),
            label=str(np.round(ydim[track_index], 3)),
        )

    left_ax.legend(title='Distance accross core:', fontsize=6)
    left_ax.set_ylabel('Distance Along Track (mm)', fontsize=8)
    left_ax.set_xlabel('Conductivity', fontsize=8)

    if str(acordc).upper() == 'DC':
        try:
            left_ax.set_xlim(0, np.percentile(array, 95) + 10 ** (-7))
        except Exception:
            print('Axis label error')

    left_ylim = left_ax.get_ylim()

    depth_edges = _centers_to_edges(depth_centers)
    if track_limits is None:
        track_left = float(np.nanmin(ydim[:track_count]))
        track_right = float(np.nanmax(ydim[:track_count]))
    else:
        track_left = float(np.nanmin(ydim[:track_count])) if track_limits[0] is None else float(track_limits[0])
        track_right = float(np.nanmax(ydim[:track_count])) if track_limits[1] is None else float(track_limits[1])
    track_edges = _track_edges_from_limits(ydim[:track_count], track_left, track_right)

    heatmap = np.array(array, copy=True)
    heatmap[button_mask] = np.nan
    heatmap = np.ma.masked_invalid(heatmap)
    scale_source = np.asarray(array, dtype=float)
    scale_source = scale_source[np.isfinite(scale_source) & ~button_mask]
    if scale_source.size:
        vmin = float(np.percentile(scale_source, 10))
        vmax = float(np.percentile(scale_source, 90))
    else:
        vmin = None
        vmax = None
    heatmap_cmap = matplotlib.colormaps.get_cmap('coolwarm').copy()
    heatmap_cmap.set_bad('black')

    mesh = right_ax.pcolormesh(
        track_edges,
        depth_edges,
        heatmap,
        cmap=heatmap_cmap,
        vmin=vmin,
        vmax=vmax,
        shading='flat',
    )
    right_ax.set_xlim(track_left, track_right)
    right_ax.set_ylim(left_ylim)
    right_ax.set_xlabel('Distance Across Core (mm)', fontsize=8)
    right_ax.set_ylabel('Distance Along Track (mm)', fontsize=8)
    right_ax.tick_params(labelsize=7)
    right_ax.set_title('Top View', fontsize=9)
    fig.colorbar(mesh, ax=right_ax, fraction=0.046, pad=0.04, label='Conductivity')

    date_dir = os.path.join(save_root, str(run_date))
    os.makedirs(date_dir, exist_ok=True)
    save_name = f"{str(core_section_face).strip()}_{str(acordc).upper()}.png"
    save_path = os.path.join(date_dir, save_name)

    fig.savefig(
        save_path,
        transparent=False,
        facecolor='white',
        dpi=450,
    )

    if show:
        plt.show()

    return fig, save_path


def _centers_to_edges(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError('No finite axis centers were provided.')
    if values.size == 1:
        span = 0.5
        return np.array([values[0] - span, values[0] + span])

    edges = np.empty(values.size + 1, dtype=float)
    midpoints = (values[1:] + values[:-1]) / 2.0
    edges[1:-1] = midpoints
    edges[0] = values[0] - (midpoints[0] - values[0])
    edges[-1] = values[-1] + (values[-1] - midpoints[-1])
    return edges


def _track_edges_from_limits(track_centers, left_limit=None, right_limit=None):
    track_centers = np.asarray(track_centers, dtype=float)
    track_centers = track_centers[np.isfinite(track_centers)]
    if track_centers.size == 0:
        raise ValueError('No finite track centers were provided.')
    if track_centers.size == 1:
        left = float(track_centers[0] - 0.5) if left_limit is None else float(left_limit)
        right = float(track_centers[0] + 0.5) if right_limit is None else float(right_limit)
        return np.array([left, right], dtype=float)

    edges = np.empty(track_centers.size + 1, dtype=float)
    edges[1:-1] = (track_centers[1:] + track_centers[:-1]) / 2.0
    edges[0] = float(track_centers[0] - (edges[1] - track_centers[0])) if left_limit is None else float(left_limit)
    edges[-1] = float(track_centers[-1] + (track_centers[-1] - edges[-2])) if right_limit is None else float(right_limit)
    return edges


def _normalize_filename(filename):
    filename = os.path.basename(str(filename).strip())
    if not filename.lower().endswith('.txt'):
        filename += '.txt'
    return filename


def _resolve_run_file(filename, data_root=os.path.join('..', 'run_outputs')):
    filename = str(filename).strip()

    if filename.lower() == 'last':
        candidates = glob.glob(os.path.join(data_root, '*', '*.txt'))
        if not candidates:
            raise FileNotFoundError(f'No .txt files were found under {data_root}')
        return max(candidates, key=os.path.getmtime)

    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    normalized = _normalize_filename(filename)
    stem = os.path.splitext(normalized)[0]
    run_date = stem[:10]

    candidate = os.path.join(data_root, run_date, normalized)
    if os.path.exists(candidate):
        return candidate

    direct_candidate = os.path.join(data_root, normalized)
    if os.path.exists(direct_candidate):
        return direct_candidate

    raise FileNotFoundError(f'Could not find run file {normalized} in {data_root}')


def _parse_run_file(file_path):
    header_row = None
    metadata = {}

    with open(file_path, 'r') as file_handle:
        for line_number, line in enumerate(file_handle):
            stripped = line.strip()
            if stripped.startswith('Index Mark Relative Depth:'):
                try:
                    metadata['index_mark'] = float(stripped.split(':', 1)[1].split(',')[0].strip())
                except Exception:
                    pass
            elif stripped.startswith('X max Position (raw - not laser corrected):'):
                try:
                    metadata['xmax'] = float(stripped.split(':', 1)[1].split(',')[0].strip())
                except Exception:
                    pass
            elif stripped.startswith('Y Left:'):
                try:
                    metadata['yl'] = float(stripped.split(':', 1)[1].split(',')[0].strip())
                except Exception:
                    pass
            elif stripped.startswith('Y Right:'):
                try:
                    metadata['yr'] = float(stripped.split(':', 1)[1].split(',')[0].strip())
                except Exception:
                    pass
            elif stripped.startswith('(first) Index Mark Absolute Depth:'):
                try:
                    metadata['top_depth'] = float(stripped.split(':', 1)[1].split(',')[0].strip())
                except Exception:
                    pass
            elif stripped.startswith('Y_dimension(mm),X_dimension(mm),Button,AC,DC,True_depth(m)'):
                header_row = line_number
                break

    if header_row is None:
        raise ValueError(f'Could not locate the data header in {file_path}')

    raw = pd.read_csv(file_path, skiprows=header_row)
    if raw.empty:
        raise ValueError(f'No data rows were found in {file_path}')

    last_row = raw.iloc[-1]
    acordc = 'AC' if str(last_row.get('AC', '')).strip() != '--' else 'DC'
    meas_col = acordc
    other_col = 'DC' if acordc == 'AC' else 'AC'

    data = raw[raw[other_col].astype(str).str.strip() == '--'].copy()
    if data.empty:
        raise ValueError(f'No {acordc} data rows were found in {file_path}')

    if 'Button' not in data.columns:
        raise ValueError(f'Button column was not found in {file_path}')

    data['Y_dimension(mm)'] = pd.to_numeric(data['Y_dimension(mm)'], errors='coerce')
    data['X_dimension(mm)'] = pd.to_numeric(data['X_dimension(mm)'], errors='coerce')
    data[meas_col] = pd.to_numeric(data[meas_col], errors='coerce')
    data['Button'] = data['Button'].astype(str).str.strip().str.lower().isin(['true', '1', 'yes'])
    data = data.dropna(subset=['Y_dimension(mm)', 'X_dimension(mm)', meas_col])

    data['_seq'] = data.groupby('Y_dimension(mm)').cumcount()
    x_wide = data.pivot(index='_seq', columns='Y_dimension(mm)', values='X_dimension(mm)')
    meas_wide = data.pivot(index='_seq', columns='Y_dimension(mm)', values=meas_col)
    button_wide = data.pivot(index='_seq', columns='Y_dimension(mm)', values='Button')

    ydim = np.asarray(x_wide.columns.to_numpy())
    xinput = x_wide.to_numpy()
    array = meas_wide.to_numpy()
    button = button_wide.to_numpy(dtype=bool)

    metadata['acordc'] = acordc
    metadata['run_date'] = os.path.basename(os.path.dirname(file_path))
    metadata['core_section_face'] = os.path.splitext(os.path.basename(file_path))[0].split('-', 5)[-1]

    return xinput, array, ydim, button, metadata


def plot_existing_run(filename, show=True, data_root=os.path.join('..', 'run_outputs'), save_root=os.path.join('..', 'figures')):
    file_path = _resolve_run_file(filename, data_root=data_root)
    xinput, array, ydim, button, metadata = _parse_run_file(file_path)

    fig, save_path = make_run_plot(
        xinput,
        array,
        ydim,
        metadata['acordc'],
        metadata['run_date'],
        metadata['core_section_face'],
        show=show,
        save_root=save_root,
        button_mask=button,
        track_limits=(metadata.get('yl'), metadata.get('yr')),
    )

    return fig, save_path, metadata




def main(filename=None):
    if filename is None:
        filename = input('Enter ECM filename to plot (or type "last" for the most recent file): ')
    fig, save_path, metadata = plot_existing_run(filename, show=True)
    print(f"Saved {metadata['acordc']} figure to {save_path}")
    return fig, save_path, metadata


if __name__ == "__main__":
    main()