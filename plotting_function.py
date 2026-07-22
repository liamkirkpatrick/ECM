# Import packages
import os
import glob

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


def make_run_plot(xinput, array, ydim, acordc, run_date, core_section_face, show=False, save_root=os.path.join('..', 'figures')):
    """Create the saved ECM summary figure and return the figure plus path."""
    array = np.asarray(array)
    ydim = np.asarray(ydim)
    xinput = np.asarray(xinput)

    if array.ndim == 1:
        array = array[:, np.newaxis]

    track_count = min(array.shape[1], len(ydim))
    cmap = matplotlib.colormaps.get_cmap('coolwarm')

    fig, (left_ax, right_ax) = plt.subplots(1, 2, figsize=(14, 8), dpi=100)

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
    left_ax.set_ylabel('Distance Along Track (mm)', fontsize=6)
    left_ax.set_xlabel('Conductivity', fontsize=6)

    if str(acordc).upper() == 'DC':
        try:
            left_ax.set_xlim(0, np.percentile(array, 95) + 10 ** (-7))
        except Exception:
            print('Axis label error')

    right_ax.set_axis_off()

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

    data['Y_dimension(mm)'] = pd.to_numeric(data['Y_dimension(mm)'], errors='coerce')
    data['X_dimension(mm)'] = pd.to_numeric(data['X_dimension(mm)'], errors='coerce')
    data[meas_col] = pd.to_numeric(data[meas_col], errors='coerce')
    data = data.dropna(subset=['Y_dimension(mm)', 'X_dimension(mm)', meas_col])

    data['_seq'] = data.groupby('Y_dimension(mm)').cumcount()
    x_wide = data.pivot(index='_seq', columns='Y_dimension(mm)', values='X_dimension(mm)')
    meas_wide = data.pivot(index='_seq', columns='Y_dimension(mm)', values=meas_col)

    ydim = np.asarray(x_wide.columns.to_numpy())
    xinput = x_wide.to_numpy()
    array = meas_wide.to_numpy()

    metadata['acordc'] = acordc
    metadata['run_date'] = os.path.basename(os.path.dirname(file_path))
    metadata['core_section_face'] = os.path.splitext(os.path.basename(file_path))[0].split('-', 5)[-1]

    return xinput, array, ydim, metadata


def plot_existing_run(filename, show=True, data_root=os.path.join('..', 'run_outputs'), save_root=os.path.join('..', 'figures')):
    file_path = _resolve_run_file(filename, data_root=data_root)
    xinput, array, ydim, metadata = _parse_run_file(file_path)

    fig, save_path = make_run_plot(
        xinput,
        array,
        ydim,
        metadata['acordc'],
        metadata['run_date'],
        metadata['core_section_face'],
        show=show,
        save_root=save_root,
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