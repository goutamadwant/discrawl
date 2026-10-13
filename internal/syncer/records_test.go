package syncer

import (
	"context"
	"path/filepath"
	"testing"

	"github.com/bwmarrin/discordgo"
	"github.com/stretchr/testify/require"

	"github.com/openclaw/discrawl/internal/store"
)

func TestToMemberRecordSkipsNilUser(t *testing.T) {
	t.Parallel()

	var rec store.MemberRecord
	require.NotPanics(t, func() {
		rec = toMemberRecord("g1", &discordgo.Member{User: nil})
	})
	require.Empty(t, rec.UserID)

	require.NotPanics(t, func() {
		rec = toMemberRecord("g1", nil)
	})
	require.Empty(t, rec.UserID)

	rec = toMemberRecord("g1", &discordgo.Member{
		User: &discordgo.User{ID: "u1", Username: "peter", GlobalName: "Peter"},
		Nick: "Pete",
	})
	require.Equal(t, "g1", rec.GuildID)
	require.Equal(t, "u1", rec.UserID)
	require.Equal(t, "peter", rec.Username)
	require.Equal(t, "Peter", rec.GlobalName)
	require.Equal(t, "Pete", rec.DisplayName)
}

func TestRefreshGuildMembersRejectsIncompleteIdentity(t *testing.T) {
	t.Parallel()

	ctx := context.Background()
	s, err := store.Open(ctx, filepath.Join(t.TempDir(), "discrawl.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = s.Close() })

	client := &fakeClient{
		members: map[string][]*discordgo.Member{
			"g1": {
				{GuildID: "g1", User: &discordgo.User{ID: "u1", Username: "peter"}},
				{GuildID: "g1", User: nil},
				nil,
			},
		},
	}
	svc := New(client, s, nil)

	var count int
	require.NotPanics(t, func() {
		count, err = svc.refreshGuildMembers(ctx, "g1", true)
	})
	require.ErrorContains(t, err, "missing user identity")
	require.Zero(t, count)

	status, err := s.Status(ctx, "db", "")
	require.NoError(t, err)
	require.Zero(t, status.MemberCount)

	rows, err := s.Members(ctx, "g1", "", 10)
	require.NoError(t, err)
	require.Empty(t, rows)
	gate, err := s.GetSyncState(ctx, guildMemberSyncSuccessScope("g1"))
	require.NoError(t, err)
	require.Empty(t, gate)
}
