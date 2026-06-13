import { Badge, Box, Flex, Text } from "@chakra-ui/react";
import type { Message } from "@/types/api";
import { hasEducationalDisclaimer } from "@/lib/chat-disclaimer";
import { SourceAttribution } from "./SourceAttribution";
import { MessageContent } from "./MessageContent";

function IconHeartbeat() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

const FOOTER_DISCLAIMER =
  "Esta orientação é educativa e não substitui um profissional de saúde.";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "USER";
  const showFooterDisclaimer = !isUser && !hasEducationalDisclaimer(message.content);

  return (
    <Flex justify={isUser ? "flex-end" : "flex-start"} mb={4}>
      <Box maxW={{ base: "92%", md: "75%" }}>

        {/* AI identity header */}
        {!isUser && (
          <Flex align="center" gap={1.5} mb={1} pl={0.5}>
            <Box
              style={{
                width: "20px",
                height: "20px",
                borderRadius: "50%",
                background: "#1D9E75",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <IconHeartbeat />
            </Box>
            <Text fontSize="11px" fontWeight="medium" color="fg.muted">
              MediClaw
            </Text>
          </Flex>
        )}

        {!isUser && message.blocked_by_guardrail && (
          <Badge colorPalette="red" mb={1} borderRadius="md">
            Resposta limitada
          </Badge>
        )}

        <Box
          bg={isUser ? "teal.500" : "bg"}
          color={isUser ? "white" : "fg"}
          px={4}
          py={3}
          borderRadius="xl"
          borderWidth={isUser ? "0" : "1px"}
          borderColor="border"
          shadow={isUser ? "sm" : "card"}
          borderBottomRightRadius={isUser ? "sm" : "xl"}
          borderBottomLeftRadius={isUser ? "xl" : "sm"}
        >
          <MessageContent content={message.content} variant={isUser ? "user" : "assistant"} />
        </Box>

        {showFooterDisclaimer && (
          <Flex align="center" gap={1} mt={1} pl={0.5}>
            <Text fontSize="10px" color="fg.muted" style={{ opacity: 0.7 }}>
              ℹ {FOOTER_DISCLAIMER}
            </Text>
          </Flex>
        )}

        {!isUser && <SourceAttribution citations={message.metadata?.citations} />}
      </Box>
    </Flex>
  );
}
