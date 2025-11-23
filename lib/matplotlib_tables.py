from matplotlib import pyplot as plt
from io import BytesIO


def create_table_matplotlib(data, headers=None, title=None) -> BytesIO:
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('tight')
    ax.axis('off')

    # Create table
    if headers:
        table_data = [headers] + data
    else:
        table_data = data

    table = plt.table(
        cellText=table_data,
        loc='center',
        cellLoc='left',
        colLoc='left'
    )

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)

    # Header styling
    if headers:
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(color='white', weight='bold')

    # Alternate row colors
    for i in range(1, len(table_data), 2):
        for j in range(len(table_data[0])):
            table[(i, j)].set_facecolor('#f5f5f5')

    # Auto-adjust column widths
    for key, cell in table.get_celld().items():
        cell.set_height(0.08)
        cell.set_edgecolor('#dddddd')

    if title:
        plt.title(title, fontsize=14, weight='bold', pad=20)

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer


if __name__ == '__main__':
    headers = [
        'CPU', 'RAM', 'ROM'
    ]
    data = [
        [1000, 40000, 10004105],
        ["LOL", "SNEAKY", "FINE"]
    ]
    image_buffer = create_table_matplotlib(
        data=data,
        headers=headers,
        title="Docker Containers"
    )

    with open('../data/tmp.png', 'wb') as f:
        f.write(image_buffer.read())
