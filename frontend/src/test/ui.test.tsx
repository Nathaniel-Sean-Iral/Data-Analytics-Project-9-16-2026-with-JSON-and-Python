import { describe, expect, it, vi } from 'vitest';
import { useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable, type Column } from '@/components/ui/table';
import { useAsync } from '@/lib/useAsync';
import { INCIDENT_TYPE_LABELS, SEVERITY_TONES, formatNumber } from '@/lib/labels';

describe('Button', () => {
  it('renders and fires its click handler', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save changes</Button>);

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not fire while disabled', async () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} disabled>
        Save changes
      </Button>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe('Badge', () => {
  it('renders its label', () => {
    render(<Badge tone="red">Critical</Badge>);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });
});

interface TestRow {
  id: number;
  name: string;
  qty: number;
}

const columns: Column<TestRow>[] = [
  { key: 'name', header: 'Name', render: (r) => r.name },
  { key: 'qty', header: 'Qty', render: (r) => String(r.qty) },
];

describe('DataTable', () => {
  it('renders rows and columns', () => {
    render(
      <DataTable
        columns={columns}
        rows={[
          { id: 1, name: 'Rice', qty: 20 },
          { id: 2, name: 'Water', qty: 5 },
        ]}
        keyFor={(r) => r.id}
      />,
    );

    expect(screen.getByText('Rice')).toBeInTheDocument();
    expect(screen.getByText('Water')).toBeInTheDocument();
  });

  it('shows the empty state when there are no rows', () => {
    render(<DataTable columns={columns} rows={[]} keyFor={() => 'x'} emptyTitle="Nothing here" />);
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
  });

  // The table is fully controlled: it reports the query and the caller supplies
  // the filtered rows, so filtering is verified from the parent's side.
  it('reports search input to onSearch and renders the rows it is given', async () => {
    function ControlledTable() {
      const [query, setQuery] = useState('');
      const rows = [
        { id: 1, name: 'Rice', qty: 20 },
        { id: 2, name: 'Water', qty: 5 },
      ].filter((r) => r.name.toLowerCase().includes(query.toLowerCase()));

      return (
        <DataTable
          columns={columns}
          rows={rows}
          keyFor={(r) => r.id}
          searchable
          searchPlaceholder="Search resources"
          onSearch={setQuery}
        />
      );
    }

    render(<ControlledTable />);
    expect(screen.getByText('Rice')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText('Search resources'), 'water');

    await waitFor(() => expect(screen.queryByText('Rice')).not.toBeInTheDocument());
    expect(screen.getByText('Water')).toBeInTheDocument();
  });

  it('shows the empty state when a search matches nothing', async () => {
    const onSearch = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[]}
        keyFor={() => 'x'}
        searchable
        searchPlaceholder="Search resources"
        onSearch={onSearch}
        emptyTitle="No records found"
      />,
    );

    await userEvent.type(screen.getByPlaceholderText('Search resources'), 'zzz');
    expect(onSearch).toHaveBeenLastCalledWith('zzz');
    expect(screen.getByText('No records found')).toBeInTheDocument();
  });
});

function Probe({ fn }: { fn: () => Promise<string> }) {
  const { data, loading, error } = useAsync(fn, []);
  if (loading) return <p>loading</p>;
  if (error) return <p role="alert">error: {error}</p>;
  return <p>result: {data}</p>;
}

describe('useAsync', () => {
  it('resolves and renders the loaded value', async () => {
    render(<Probe fn={async () => 'loaded'} />);
    expect(await screen.findByText('result: loaded')).toBeInTheDocument();
  });

  it('surfaces the error message when the loader rejects', async () => {
    render(<Probe fn={async () => { throw new Error('boom'); }} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('error: boom');
  });
});

describe('labels', () => {
  it('maps incident types to human labels', () => {
    expect(INCIDENT_TYPE_LABELS.flood).toBe('Flood');
    expect(INCIDENT_TYPE_LABELS.earthquake).toBe('Earthquake');
  });

  it('assigns the red tone to critical severity', () => {
    expect(SEVERITY_TONES.critical).toBe('red');
  });

  it('formats numbers for the locale', () => {
    expect(formatNumber(1234)).toBe('1,234');
  });
});
