import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { App } from './App';

describe('YETI Ad Generator UI', () => {
  it('valid JSON reveals six audiences, three formats, and 18 outputs', () => {
    render(<App />);

    // Check header
    expect(screen.getByText('AD GENERATOR')).toBeInTheDocument();

    // Check formula / summary banner: "6 audiences × 3 formats = 18 outputs"
    expect(screen.getByText(/6 audiences/i)).toBeInTheDocument();
    expect(screen.getByText(/3 formats/i)).toBeInTheDocument();
    expect(screen.getByText(/18 outputs/i)).toBeInTheDocument();

    // Check 3 target formats
    expect(screen.getByText('1:1')).toBeInTheDocument();
    expect(screen.getByText('16:9')).toBeInTheDocument();
    expect(screen.getByText('9:16')).toBeInTheDocument();

    // Check 6 audience personas P01 - P06
    expect(screen.getByText('P01')).toBeInTheDocument();
    expect(screen.getByText('Westwood College Tailgaters')).toBeInTheDocument();

    expect(screen.getByText('P02')).toBeInTheDocument();
    expect(screen.getByText('South Central College Tailgaters')).toBeInTheDocument();

    expect(screen.getByText('P03')).toBeInTheDocument();
    expect(screen.getByText('Westside Recent Graduates')).toBeInTheDocument();

    expect(screen.getByText('P04')).toBeInTheDocument();
    expect(screen.getByText('College Friends Beach Day')).toBeInTheDocument();

    expect(screen.getByText('P05')).toBeInTheDocument();
    expect(screen.getByText('First-Time Family Campers')).toBeInTheDocument();

    expect(screen.getByText('P06')).toBeInTheDocument();
    expect(screen.getByText('Graduate Adventure Campers')).toBeInTheDocument();

    // Check Generate button with 18 outputs
    const generateBtn = screen.getByRole('button', { name: /GENERATE 18 ADS/i });
    expect(generateBtn).toBeInTheDocument();
    expect(generateBtn).not.toBeDisabled();

    // Click generate button and verify pipeline announcement
    fireEvent.click(generateBtn);
    expect(screen.getByText(/UI ready — connect pipeline next/i)).toBeInTheDocument();
  });

  it('inspect / edit JSON panel expands and displays editable JSON', () => {
    render(<App />);

    const toggleBtn = screen.getByRole('button', { name: /INSPECT \/ EDIT JSON/i });
    expect(toggleBtn).toBeInTheDocument();

    fireEvent.click(toggleBtn);

    const textarea = screen.getByLabelText(/Edit campaign JSON content/i) as HTMLTextAreaElement;
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toContain('yeti-la-go-anywhere-2026');
  });
});
