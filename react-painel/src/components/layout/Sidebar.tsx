"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Flex, Text } from "@chakra-ui/react";
import { useAuth } from "@/context/AuthContext";

// ─── SVG Icons ───────────────────────────────────────────────────────────────

function IconMessage() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function IconUsers() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function IconBook() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );
}

function IconChart() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function IconLogout() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function IconCollapseLeft() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M11 19l-7-7 7-7" />
      <path d="M20 5v14" />
    </svg>
  );
}

function IconExpandRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M13 5l7 7-7 7" />
      <path d="M4 19V5" />
    </svg>
  );
}

// ─── Constants ────────────────────────────────────────────────────────────────

const BG = "#0F6E56";
const ACTIVE_BG = "rgba(255,255,255,0.12)";
const HOVER_BG = "rgba(255,255,255,0.08)";
const ACTIVE_BORDER = "#9FE1CB";
const TEXT_WHITE = "#ffffff";
const TEXT_MUTED = "rgba(255,255,255,0.55)";
const TEXT_LABEL = "rgba(255,255,255,0.3)";
const DIVIDER = "rgba(255,255,255,0.1)";

// ─── Types ────────────────────────────────────────────────────────────────────

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

export interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

// ─── Nav data ─────────────────────────────────────────────────────────────────

const navItems: NavItem[] = [
  { label: "Chat IA", href: "/chat", icon: <IconMessage /> },
  { label: "Pacientes", href: "/patients", icon: <IconUsers /> },
  { label: "Conhecimento", href: "/conhecimento", icon: <IconBook /> },
];

const adminItems: NavItem[] = [
  { label: "Métricas", href: "/admin/metrics", icon: <IconChart />, adminOnly: true },
];

// ─── NavLink ──────────────────────────────────────────────────────────────────

function NavLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
  const [hovered, setHovered] = useState(false);

  const bg = isActive ? ACTIVE_BG : hovered ? HOVER_BG : "transparent";
  const color = isActive || hovered ? TEXT_WHITE : TEXT_MUTED;

  return (
    <Box
      as={Link}
      href={item.href}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: collapsed ? 0 : "10px",
        padding: collapsed ? "9px 0" : "8px 12px",
        margin: "1px 8px",
        borderRadius: "8px",
        background: bg,
        color,
        borderRight: `2px solid ${isActive ? ACTIVE_BORDER : "transparent"}`,
        textDecoration: "none",
        transition: "background 0.12s, color 0.12s",
        justifyContent: collapsed ? "center" : "flex-start",
        overflow: "hidden",
        minHeight: "36px",
        whiteSpace: "nowrap",
      }}
      title={collapsed ? item.label : undefined}
    >
      <Box style={{ display: "flex", alignItems: "center", flexShrink: 0, color: "inherit" }}>
        {item.icon}
      </Box>
      {!collapsed && (
        <Text
          fontSize="sm"
          fontWeight={isActive ? "semibold" : "medium"}
          style={{ color: "inherit", overflow: "hidden", textOverflow: "ellipsis" }}
        >
          {item.label}
        </Text>
      )}
    </Box>
  );
}

// ─── SidebarContent ───────────────────────────────────────────────────────────

export function SidebarContent({ collapsed, onToggle }: SidebarProps) {
  const { user, logout } = useAuth();
  const [settingsHovered, setSettingsHovered] = useState(false);
  const [logoutHovered, setLogoutHovered] = useState(false);

  const initials = user ? `${user.first_name?.[0] ?? ""}`.toUpperCase() : "?";

  return (
    <Flex direction="column" h="full" style={{ background: BG, overflow: "hidden" }}>

      {/* ── Header ── */}
      <Flex
        align="center"
        justify={collapsed ? "center" : "space-between"}
        style={{
          borderBottom: `1px solid ${DIVIDER}`,
          padding: collapsed ? "14px 0" : "12px 12px 12px 16px",
          minHeight: "56px",
          flexShrink: 0,
        }}
      >
        {!collapsed && (
          <Box>
            <Text fontWeight="semibold" fontSize="sm" style={{ color: TEXT_WHITE, lineHeight: "1.2" }}>
              MediClaw
            </Text>
            <Text fontSize="xs" style={{ color: TEXT_MUTED, marginTop: "2px" }}>
              Assistente de saúde
            </Text>
          </Box>
        )}
        <Box
          as="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
          title={collapsed ? "Expandir menu" : "Recolher menu"}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "28px",
            height: "28px",
            borderRadius: "6px",
            color: TEXT_MUTED,
            background: "transparent",
            border: "none",
            cursor: "pointer",
            flexShrink: 0,
            transition: "color 0.12s",
          }}
        >
          {collapsed ? <IconExpandRight /> : <IconCollapseLeft />}
        </Box>
      </Flex>

      {/* ── Nav ── */}
      <Box flex={1} py={2} style={{ overflowY: "auto", overflowX: "hidden" }}>
        {!collapsed && (
          <Text
            style={{
              color: TEXT_LABEL,
              fontSize: "10px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              padding: "6px 16px 4px",
              display: "block",
            }}
          >
            Principal
          </Text>
        )}

        {navItems.map((item) => (
          <NavLink key={item.href} item={item} collapsed={collapsed} />
        ))}

        {user?.role === "ADMIN" && (
          <>
            {!collapsed && (
              <Text
                style={{
                  color: TEXT_LABEL,
                  fontSize: "10px",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  padding: "12px 16px 4px",
                  display: "block",
                }}
              >
                Admin
              </Text>
            )}
            {adminItems.map((item) => (
              <NavLink key={item.href} item={item} collapsed={collapsed} />
            ))}
          </>
        )}
      </Box>

      {/* ── Bottom ── */}
      <Box style={{ borderTop: `1px solid ${DIVIDER}`, paddingTop: "4px", paddingBottom: "8px", flexShrink: 0 }}>
        {/* Settings */}
        <Box
          as="button"
          onMouseEnter={() => setSettingsHovered(true)}
          onMouseLeave={() => setSettingsHovered(false)}
          title="Configurações"
          aria-label="Configurações"
          style={{
            display: "flex",
            alignItems: "center",
            gap: collapsed ? 0 : "10px",
            padding: collapsed ? "9px 0" : "8px 12px",
            margin: "1px 8px",
            borderRadius: "8px",
            background: settingsHovered ? HOVER_BG : "transparent",
            color: settingsHovered ? TEXT_WHITE : TEXT_MUTED,
            border: "none",
            cursor: "pointer",
            width: "calc(100% - 16px)",
            justifyContent: collapsed ? "center" : "flex-start",
            transition: "background 0.12s, color 0.12s",
            minHeight: "36px",
            whiteSpace: "nowrap",
          }}
        >
          <Box style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
            <IconSettings />
          </Box>
          {!collapsed && (
            <Text fontSize="sm" style={{ color: "inherit" }}>
              Configurações
            </Text>
          )}
        </Box>

        {/* User row */}
        <Flex
          align="center"
          gap={collapsed ? 0 : 2}
          style={{
            padding: collapsed ? "8px 0" : "8px 12px",
            margin: "1px 8px",
            justifyContent: collapsed ? "center" : "flex-start",
          }}
        >
          <Box
            title={collapsed ? user?.first_name : undefined}
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "rgba(255,255,255,0.18)",
              color: TEXT_WHITE,
              fontSize: "11px",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {initials}
          </Box>

          {!collapsed && (
            <Text
              fontSize="xs"
              fontWeight="medium"
              flex={1}
              style={{
                color: "rgba(255,255,255,0.8)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {user?.first_name}
            </Text>
          )}

          {!collapsed && (
            <Box
              as="button"
              onClick={logout}
              onMouseEnter={() => setLogoutHovered(true)}
              onMouseLeave={() => setLogoutHovered(false)}
              aria-label="Sair"
              title="Sair"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "4px",
                borderRadius: "5px",
                background: logoutHovered ? "rgba(255,255,255,0.1)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: logoutHovered ? TEXT_WHITE : TEXT_MUTED,
                transition: "background 0.12s, color 0.12s",
                flexShrink: 0,
              }}
            >
              <IconLogout />
            </Box>
          )}
        </Flex>
      </Box>
    </Flex>
  );
}
